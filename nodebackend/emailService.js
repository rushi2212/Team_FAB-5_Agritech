/**
 * Email Service using Nodemailer
 * Provides email sending functionality for pest/disease alerts
 */
import nodemailer from 'nodemailer';
import dotenv from 'dotenv';

dotenv.config();

// Email configuration
const SMTP_HOST = process.env.SMTP_HOST || 'smtp.gmail.com';
const SMTP_PORT = parseInt(process.env.SMTP_PORT) || 587;
const SMTP_USER = process.env.SMTP_USER || '';
const SMTP_PASSWORD = process.env.SMTP_PASSWORD || '';
const ALERT_FROM_EMAIL = process.env.ALERT_FROM_EMAIL || SMTP_USER;

// Create transporter
let transporter = null;

function createTransporter() {
  if (!SMTP_USER || !SMTP_PASSWORD) {
    console.warn('[Email Service] SMTP credentials not configured');
    return null;
  }

  try {
    transporter = nodemailer.createTransport({
      host: SMTP_HOST,
      port: SMTP_PORT,
      secure: false, // Use TLS
      auth: {
        user: SMTP_USER,
        pass: SMTP_PASSWORD,
      },
    });

    console.log('[Email Service] Transporter created successfully');
    return transporter;
  } catch (error) {
    console.error('[Email Service] Failed to create transporter:', error.message);
    return null;
  }
}

/**
 * Send pest/disease alert email
 * @param {Object} riskData - Risk assessment data
 * @param {string} recipientEmail - Recipient email address
 * @returns {Promise<boolean>} - Success status
 */
export async function sendPestAlert(riskData, recipientEmail) {
  if (!recipientEmail) {
    console.log('[Email Service] No recipient email provided');
    return false;
  }

  const transport = transporter || createTransporter();
  if (!transport) {
    console.log('[Email Service] Email service not configured');
    return false;
  }

  try {
    // Generate risk color based on level
    const riskColors = {
      low: '#4caf50',
      medium: '#ff9800',
      high: '#f44336',
      critical: '#d32f2f'
    };
    const riskColor = riskColors[riskData.risk_level] || '#f44336';

    // Create HTML email
    const html = `
      <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #f5f5f5;">
          <div style="background: ${riskColor}; color: white; padding: 20px; text-align: center;">
            <h1 style="margin: 0;">⚠️ Crop Health Alert</h1>
          </div>
          
          <div style="padding: 20px; background: white; margin-top: 2px;">
            <h2 style="color: #333;">Risk Assessment for ${riskData.crop_name}</h2>
            <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 15px 0;">
              <p style="margin: 5px 0;"><strong>Crop Stage:</strong> ${riskData.crop_stage} (Day ${riskData.day_of_cycle})</p>
              <p style="margin: 5px 0;">
                <strong>Risk Level:</strong> 
                <span style="color: ${riskColor}; font-size: 20px; font-weight: bold;">
                  ${riskData.risk_level.toUpperCase()}
                </span> 
                (${riskData.risk_score}/100)
              </p>
            </div>
            
            <h3 style="color: #333; border-bottom: 2px solid #4caf50; padding-bottom: 5px;">
              🌡️ Weather Conditions
            </h3>
            <ul style="line-height: 1.8;">
              <li><strong>Temperature:</strong> ${riskData.weather_factors.temperature_c}°C</li>
              <li><strong>Humidity:</strong> ${riskData.weather_factors.humidity_percent}%</li>
              <li><strong>Rainfall:</strong> ${riskData.weather_factors.rainfall_mm}mm</li>
            </ul>
            
            ${riskData.pest_risks && riskData.pest_risks.length > 0 ? `
            <h3 style="color: #333; border-bottom: 2px solid #ff9800; padding-bottom: 5px;">
              🐛 Pest Risks
            </h3>
            <ul style="line-height: 1.8;">
              ${riskData.pest_risks.map(p => `
                <li>
                  <strong>${p.name}</strong> 
                  <span style="color: ${riskColors[p.severity]};">(${p.severity})</span>
                  <br/><em>${p.description}</em>
                </li>
              `).join('')}
            </ul>
            ` : ''}
            
            ${riskData.disease_risks && riskData.disease_risks.length > 0 ? `
            <h3 style="color: #333; border-bottom: 2px solid #f44336; padding-bottom: 5px;">
              🦠 Disease Risks
            </h3>
            <ul style="line-height: 1.8;">
              ${riskData.disease_risks.map(d => `
                <li>
                  <strong>${d.name}</strong> 
                  <span style="color: ${riskColors[d.severity]};">(${d.severity})</span>
                  <br/><em>${d.description}</em>
                </li>
              `).join('')}
            </ul>
            ` : ''}
            
            <h3 style="color: #333; border-bottom: 2px solid #2196f3; padding-bottom: 5px;">
              🛡️ Recommended Actions
            </h3>
            <ol style="line-height: 1.8; padding-left: 20px;">
              ${riskData.preventive_actions.map(action => `<li>${action}</li>`).join('')}
            </ol>
            
            <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin-top: 20px; border-radius: 3px;">
              <strong>⚠️ Important:</strong> Take immediate action to protect your crop. 
              Contact your local agricultural extension officer for specific treatment recommendations.
            </div>
          </div>
          
          <div style="background: #333; color: white; padding: 15px; text-align: center; font-size: 12px; margin-top: 2px;">
            <p style="margin: 5px 0;">Agritech FAB-5 Early Warning System</p>
            <p style="margin: 5px 0;">Generated on ${riskData.last_updated}</p>
          </div>
        </body>
      </html>
    `;

    // Email options
    const mailOptions = {
      from: `"Agritech Alert System" <${ALERT_FROM_EMAIL}>`,
      to: recipientEmail,
      subject: `🚨 ${riskData.risk_level.toUpperCase()} Risk Alert: ${riskData.crop_name}`,
      html: html,
    };

    // Send email
    console.log(`[Email Service] Sending alert to ${recipientEmail}...`);
    const info = await transport.sendMail(mailOptions);
    console.log(`[Email Service] ✓ Email sent successfully: ${info.messageId}`);
    
    return true;
  } catch (error) {
    console.error('[Email Service] ✗ Failed to send email:', error.message);
    return false;
  }
}

/**
 * Verify email configuration
 * @returns {Promise<boolean>} - Whether email is configured correctly
 */
export async function verifyEmailConfig() {
  const transport = transporter || createTransporter();
  if (!transport) {
    return false;
  }

  try {
    await transport.verify();
    console.log('[Email Service] ✓ Email configuration verified');
    return true;
  } catch (error) {
    console.error('[Email Service] ✗ Email verification failed:', error.message);
    return false;
  }
}

// Initialize transporter on module load
createTransporter();
