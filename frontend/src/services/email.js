const { Resend } = require('resend');

const resend = new Resend(process.env.RESEND_API_KEY);

const sendEmail = async ({ to, subject, html }) => {
  try {
    const { data, error } = await resend.emails.send({
      from: process.env.EMAIL_FROM || 'Your App <onboarding@resend.dev>',
      to: [to],
      subject,
      html,
    });

    if (error) {
      console.error('Resend error:', error);
      throw new Error(error.message);
    }

    console.log('Email sent:', data.id);
    return data;
  } catch (err) {
    console.error('Failed to send email:', err);
    throw err;
  }
};

module.exports = { sendEmail };