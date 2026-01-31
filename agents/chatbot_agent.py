"""
Farmer Interaction / Chatbot Agent

Role: Human-friendly conversational interface for farmers
- Integrates all agent outputs (crop, calendar, market, pest/disease)
- Answers farmer questions in simple language
- Provides context-aware explanations
- Cites government sources for credibility
"""

import json
import os
from typing import Dict, List, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Import existing agents
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.market_price_agent import get_price_prediction
from agents.pest_disease_agent import assess_pest_disease_risk


class ChatbotAgent:
    """
    Conversational agent that orchestrates all farming agents and provides
    human-friendly responses with government source citations.
    """
    
    def __init__(self, api_key: str, data_dir: str = "data"):
        """
        Initialize the chatbot agent.
        
        Args:
            api_key: OpenAI API key
            data_dir: Directory containing variable.json, calendar.json, persistent.json
        """
        self.data_dir = data_dir
        self.api_key = api_key
        
        # Initialize LLM (GPT-4o for better reasoning and cost balance)
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.7,  # Slightly creative for natural conversation
            api_key=api_key
        )
        
        # Store conversation history
        self.conversation_history = []
        
        # System prompt
        self.system_prompt = """You are a helpful farming assistant for Indian farmers. Your role is to:

1. **Speak in simple, clear language** - Avoid technical jargon. Explain concepts in everyday terms.
2. **Be context-aware** - Use the provided context about the farmer's current situation (crop, location, day of cycle).
3. **Cite government sources** - Always mention sources like TNAU, ICAR, Agmarknet, etc.
4. **Be practical and actionable** - Give specific, actionable advice that farmers can implement.
5. **Show empathy** - Understand that farming is challenging. Be encouraging and supportive.
6. **Explain "why"** - Don't just say what to do, explain why it's important.

When answering:
- Use the provided context data to give accurate, relevant answers
- Provide clear, step-by-step guidance when needed
- Use examples and analogies when explaining complex concepts
- Always cite sources at the end of your response
- If you don't have enough information, ask clarifying questions"""
        
    def _load_json(self, filename: str) -> Dict:
        """Load JSON file from data directory."""
        filepath = os.path.join(self.data_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _get_current_context(self) -> Dict:
        """Get current farmer's context from data files."""
        variable = self._load_json("variable.json")
        calendar = self._load_json("calendar.json")
        
        if not variable:
            return {
                "status": "no_data",
                "message": "No farm data found. Please set up your farm profile first."
            }
        
        day_of_cycle = variable.get("day_of_cycle", 1)
        current_task = None
        current_stage = None
        
        if calendar and "days" in calendar:
            days = calendar["days"]
            for day in days:
                if day.get("day") == day_of_cycle:
                    current_task = day.get("tasks", [])
                    current_stage = day.get("stage", "Unknown")
                    break
        
        return {
            "status": "ok",
            "crop": variable.get("crop", {}).get("name", "Unknown"),
            "season": variable.get("crop", {}).get("season", "Unknown"),
            "location": f"{variable.get('location', {}).get('city', 'Unknown')}, {variable.get('location', {}).get('state', 'Unknown')}",
            "day_of_cycle": day_of_cycle,
            "current_stage": current_stage,
            "today_tasks": current_task,
            "weather": variable.get("climate", {}),
            "soil_type": variable.get("soil", {}).get("usda_texture_class", "Unknown")
        }
    
    def _get_detailed_context(self, user_query: str) -> str:
        """Get detailed context based on user query."""
        context = self._get_current_context()
        
        if context["status"] == "no_data":
            return context["message"]
        
        variable = self._load_json("variable.json")
        calendar = self._load_json("calendar.json")
        persistent = self._load_json("persistent.json")
        
        # Build context string
        context_str = f"""**Current Farm Status:**
- Crop: {context['crop']} ({context['season']} season)
- Location: {context['location']}
- Day of Cycle: Day {context['day_of_cycle']}
- Current Stage: {context['current_stage']}
- Soil Type: {context['soil_type']}

**Today's Weather:**
- Temperature: {context['weather'].get('temperature_2m', 'N/A')}°C
- Humidity: {context['weather'].get('relative_humidity_2m', 'N/A')}%
- Rainfall: {context['weather'].get('precipitation', 'N/A')}mm

**Today's Tasks:**
"""
        if context['today_tasks']:
            for task in context['today_tasks']:
                context_str += f"- {task}\n"
        else:
            context_str += "- No tasks scheduled for today\n"
        
        # Add additional context based on query keywords
        query_lower = user_query.lower()
        
        # Calendar/tasks information
        if any(word in query_lower for word in ['calendar', 'task', 'schedule', 'upcoming', 'next', 'tomorrow']):
            if calendar and "days" in calendar:
                days = calendar["days"]
                day_of_cycle = context["day_of_cycle"]
                context_str += "\n**Upcoming Tasks (Next 3 Days):**\n"
                for day in days:
                    if day.get("day", 0) > day_of_cycle and day.get("day", 0) <= day_of_cycle + 3:
                        day_num = day.get("day")
                        stage = day.get("stage", "Unknown")
                        tasks = day.get("tasks", [])
                        context_str += f"\nDay {day_num} - {stage}:\n"
                        for task in tasks:
                            context_str += f"  - {task}\n"
        
        # Market price information
        if any(word in query_lower for word in ['price', 'market', 'sell', 'harvest']):
            try:
                crop_name = variable.get("crop", {}).get("name", "")
                state = variable.get("location", {}).get("state", "")
                season = variable.get("crop", {}).get("season", "")
                
                prediction = get_price_prediction(crop_name, state, season, "March")
                context_str += f"""\n**Market Price Prediction:**
- Average Price: ₹{prediction['average_price']:.2f} per quintal
- Price Range: ₹{prediction['price_range']['min']:.2f} - ₹{prediction['price_range']['max']:.2f}
- Trend: {prediction['trend'].upper()}
- Confidence: {prediction['confidence'].upper()}
*Source: Agmarknet (Government of India)*
"""
            except Exception as e:
                context_str += f"\n(Market price data temporarily unavailable)\n"
        
        # Pest/disease information
        if any(word in query_lower for word in ['pest', 'disease', 'risk', 'insect', 'fungus', 'problem']):
            try:
                current_stage = context.get("current_stage", "Unknown")
                risk_assessment = assess_pest_disease_risk(variable, current_stage)
                context_str += f"""\n**Pest & Disease Risk:**
- Risk Level: {risk_assessment['overall_risk_level'].upper()}
- Risk Score: {risk_assessment['risk_score']}/100
"""
                if risk_assessment['pests']:
                    context_str += "- Pest Risks: " + ", ".join([p['name'] for p in risk_assessment['pests']]) + "\n"
                if risk_assessment['diseases']:
                    context_str += "- Disease Risks: " + ", ".join([d['name'] for d in risk_assessment['diseases']]) + "\n"
                context_str += "*Source: ICAR Integrated Pest Management guidelines*\n"
            except Exception as e:
                context_str += f"\n(Pest risk data temporarily unavailable)\n"
        
        # Crop information
        if any(word in query_lower for word in ['fertilizer', 'pesticide', 'stage', 'growth', 'cultivation']):
            crop_name = variable.get("crop", {}).get("name", "")
            state = variable.get("location", {}).get("state", "")
            
            if persistent and crop_name and state in persistent.get(crop_name, {}):
                crop_data = persistent[crop_name][state]
                context_str += f"""\n**Crop Information:**
- Cycle Duration: {crop_data.get('cycle_duration_days', 'N/A')} days
- Growth Stages: {', '.join([s['name'] for s in crop_data.get('stages', [])])}
*Source: {crop_data.get('source', 'TNAU Agritech Portal, ICAR')}*
"""
        
        return context_str
    
    def chat(self, message: str) -> Dict[str, Any]:
        """
        Process a chat message and return response with sources.
        
        Args:
            message: User's question or message
            
        Returns:
            Dict with:
                - response: Agent's answer
                - sources: List of sources cited
                - tools_used: List of tools invoked
        """
        try:
            # Get context based on query
            context_info = self._get_detailed_context(message)
            
            # Build messages for LLM
            messages = [SystemMessage(content=self.system_prompt)]
            
            # Add conversation history
            for msg in self.conversation_history[-10:]:  # Last 10 messages
                messages.append(msg)
            
            # Add current user message with context
            user_message_with_context = f"""User Question: {message}

**Current Farm Context:**
{context_info}

Please answer the user's question using the provided context. Always cite your sources (TNAU, ICAR, Agmarknet, etc.) at the end of your response."""
            
            messages.append(HumanMessage(content=user_message_with_context))
            
            # Get response from LLM
            response = self.llm.invoke(messages)
            response_text = response.content
            
            # Extract sources from response
            sources = []
            source_keywords = [
                "TNAU", "ICAR", "Agmarknet", "Open-Meteo", "SoilGrids",
                "Government of India", "State Agriculture", "ISRIC"
            ]
            for keyword in source_keywords:
                if keyword in response_text:
                    if keyword == "TNAU":
                        sources.append("TNAU Agritech Portal")
                    elif keyword == "ICAR":
                        sources.append("ICAR guidelines")
                    elif keyword == "Agmarknet":
                        sources.append("Agmarknet (Government of India)")
                    elif keyword == "Open-Meteo":
                        sources.append("Open-Meteo Weather API")
                    elif keyword == "SoilGrids":
                        sources.append("SoilGrids (ISRIC World Soil Information)")
            
            # Remove duplicates
            sources = list(set(sources))
            
            # Update conversation history
            self.conversation_history.append(HumanMessage(content=message))
            self.conversation_history.append(AIMessage(content=response_text))
            
            # Keep only last 20 messages
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            context = self._get_current_context()
            
            return {
                "response": response_text,
                "sources": sources if sources else ["General farming knowledge"],
                "tools_used": [],
                "context": context if context["status"] == "ok" else None
            }
            
        except Exception as e:
            return {
                "response": f"I'm sorry, I encountered an error: {str(e)}. Please try asking in a different way.",
                "sources": [],
                "tools_used": [],
                "error": str(e)
            }
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history."""
        try:
            history = []
            for msg in self.conversation_history:
                if isinstance(msg, HumanMessage):
                    history.append({
                        "role": "user",
                        "content": msg.content
                    })
                elif isinstance(msg, AIMessage):
                    history.append({
                        "role": "assistant",
                        "content": msg.content
                    })
            return history
        except:
            return []
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
    
    def get_quick_suggestions(self) -> List[str]:
        """Get context-aware quick action suggestions."""
        context = self._get_current_context()
        
        if context["status"] == "no_data":
            return [
                "How do I set up my farm profile?",
                "What crops can I grow in my region?",
                "Tell me about soil testing"
            ]
        
        suggestions = [
            "What should I do today?",
            "When is harvest time?",
            "What are the market prices?",
            "Is there any pest risk?",
            "Show me my farming calendar"
        ]
        
        # Add context-specific suggestions
        if context.get("current_stage"):
            stage = context["current_stage"]
            if "flowering" in stage.lower():
                suggestions.append("How do I protect flowers from pests?")
            elif "harvest" in stage.lower():
                suggestions.append("What's the best time to harvest?")
        
        return suggestions[:6]  # Return max 6 suggestions


# Standalone function for API integration
def create_chatbot(api_key: str, data_dir: str = "data") -> ChatbotAgent:
    """Factory function to create a chatbot instance."""
    return ChatbotAgent(api_key, data_dir)


if __name__ == "__main__":
    # Test the chatbot
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment")
        exit(1)
    
    chatbot = create_chatbot(api_key)
    
    print("🌾 Farmer Chatbot Agent Initialized!")
    print("Type 'quit' to exit, 'history' to see conversation, 'clear' to reset\n")
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() == 'quit':
            break
        elif user_input.lower() == 'history':
            history = chatbot.get_history()
            print("\n--- Conversation History ---")
            for msg in history:
                print(f"{msg['role'].upper()}: {msg['content']}")
            print("----------------------------\n")
            continue
        elif user_input.lower() == 'clear':
            chatbot.clear_history()
            print("✓ Conversation history cleared\n")
            continue
        
        if not user_input:
            continue
        
        print("\n🤖 Assistant: ", end="")
        result = chatbot.chat(user_input)
        print(result['response'])
        
        if result['sources']:
            print("\n📚 Sources:", ", ".join(result['sources']))
        print()
