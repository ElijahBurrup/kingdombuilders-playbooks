import resend

import config
from database import get_purchase_by_token, log_email

resend.api_key = config.RESEND_API_KEY

FROM_EMAIL = "The Conductor's Playbook <playbook@kingdombuilders.ai>"


def send_delivery_email(customer_email, download_token):
    """Email 1: Immediate delivery with download link."""
    download_url = f"{config.BASE_URL}/download/{download_token}"

    html = f"""
    <div style="max-width:600px;margin:0 auto;font-family:Arial,Helvetica,sans-serif;background:#FAF6ED;padding:40px 24px;">
      <div style="text-align:center;margin-bottom:32px;">
        <div style="font-size:11px;font-weight:600;letter-spacing:3px;text-transform:uppercase;color:#7B4FBF;">Kingdom Builders AI</div>
      </div>

      <div style="background:linear-gradient(135deg,#1A0A2E 0%,#2D1B4E 100%);border-radius:8px;padding:40px 32px;text-align:center;">
        <h1 style="font-family:Georgia,serif;font-size:28px;color:#FFFFFF;margin:0 0 8px;">Your Playbook is Ready</h1>
        <p style="font-size:15px;color:rgba(255,255,255,0.5);margin:0 0 32px;">Thank you for your purchase. Here's your download link.</p>

        <a href="{download_url}" style="display:inline-block;padding:16px 48px;background:linear-gradient(135deg,#D4A843 0%,#E8C96A 100%);color:#1A0A2E;font-size:16px;font-weight:700;text-decoration:none;border-radius:4px;">
          DOWNLOAD YOUR PLAYBOOK
        </a>

        <p style="font-size:13px;color:rgba(255,255,255,0.3);margin-top:24px;">
          You have 5 downloads available over the next 30 days.
        </p>
      </div>

      <div style="margin-top:32px;padding:24px;background:#FFFFFF;border-radius:8px;border:1px solid rgba(74,45,122,0.08);">
        <h2 style="font-family:Georgia,serif;font-size:20px;color:#1A0A2E;margin:0 0 12px;">What to do first</h2>
        <p style="font-size:15px;color:#3A2A55;line-height:1.7;margin:0;">
          Start with <strong>Model 01: The Conductor Model</strong>. Read through the identity shift framework, then try the 80/20 Inversion on your very next AI session. You'll feel the difference immediately.
        </p>
      </div>

      <div style="text-align:center;margin-top:32px;font-size:12px;color:#6B5A8A;">
        <p>Questions? Reply to this email or contact support@kingdombuilders.ai</p>
        <p style="margin-top:16px;font-style:italic;color:rgba(107,90,138,0.5);">
          "Whatever you do, work at it with all your heart." — Colossians 3:23
        </p>
      </div>
    </div>
    """

    try:
        result = resend.Emails.send({
            "from": FROM_EMAIL,
            "to": customer_email,
            "subject": "Your Conductor's Playbook is ready",
            "html": html,
        })
        purchase = get_purchase_by_token(download_token)
        if purchase:
            log_email(purchase["id"], "delivery", result.get("id") if isinstance(result, dict) else None)
    except Exception as e:
        print(f"Failed to send delivery email to {customer_email}: {e}")


def send_quickstart_email(customer_email, download_token):
    """Email 2: Quick Start Guide (sent 24 hours after purchase)."""
    download_url = f"{config.BASE_URL}/download/{download_token}"

    html = f"""
    <div style="max-width:600px;margin:0 auto;font-family:Arial,Helvetica,sans-serif;background:#FAF6ED;padding:40px 24px;">
      <div style="text-align:center;margin-bottom:32px;">
        <div style="font-size:11px;font-weight:600;letter-spacing:3px;text-transform:uppercase;color:#7B4FBF;">Kingdom Builders AI</div>
      </div>

      <div style="padding:0 8px;">
        <h1 style="font-family:Georgia,serif;font-size:24px;color:#1A0A2E;margin:0 0 20px;">Your first Conductor session</h1>

        <p style="font-size:15px;color:#3A2A55;line-height:1.8;margin:0 0 20px;">
          You've had the Playbook for 24 hours. Here's how to make your first session count.
        </p>

        <div style="background:#FFFFFF;border-radius:8px;padding:24px;border-left:4px solid #D4A843;margin:24px 0;">
          <p style="font-size:15px;color:#3A2A55;line-height:1.7;margin:0;">
            <strong>The Quick Start:</strong> Open your AI tool. Before typing anything, spend 60 seconds writing down exactly what you want to exist at the end of this session. Not what you want the AI to do — what you want to <em>have</em> when you're done. That's your seed. Now give it to the AI as a specification, not a request.
          </p>
        </div>

        <p style="font-size:15px;color:#3A2A55;line-height:1.8;margin:0 0 20px;">
          Notice the difference? You're not prompting — you're specifying. You're not waiting for output — you're steering toward a known destination. That's the Conductor mindset, and it starts with those 60 seconds.
        </p>

        <p style="font-size:15px;color:#3A2A55;line-height:1.8;margin:0 0 24px;">
          Try it three times today. Track how many rounds it takes to get to "done." That's your convergence rate — and watching it drop is the most satisfying metric you've ever tracked.
        </p>

        <div style="text-align:center;">
          <a href="{download_url}" style="display:inline-block;padding:14px 36px;background:linear-gradient(135deg,#D4A843 0%,#E8C96A 100%);color:#1A0A2E;font-size:15px;font-weight:700;text-decoration:none;border-radius:4px;">
            RE-DOWNLOAD THE PLAYBOOK
          </a>
        </div>
      </div>

      <div style="text-align:center;margin-top:32px;font-size:12px;color:#6B5A8A;">
        <p>Questions? Reply to this email or contact support@kingdombuilders.ai</p>
        <p style="margin-top:8px;font-size:11px;color:rgba(107,90,138,0.3);">
          You're receiving this because you purchased The Conductor's Playbook.<br>
          <a href="mailto:support@kingdombuilders.ai?subject=Unsubscribe" style="color:rgba(107,90,138,0.4);">Unsubscribe from follow-up emails</a>
        </p>
      </div>
    </div>
    """

    try:
        result = resend.Emails.send({
            "from": FROM_EMAIL,
            "to": customer_email,
            "subject": "Start here: Your first Conductor session",
            "html": html,
        })
        purchase = get_purchase_by_token(download_token)
        if purchase:
            log_email(purchase["id"], "quickstart", result.get("id") if isinstance(result, dict) else None)
    except Exception as e:
        print(f"Failed to send quickstart email to {customer_email}: {e}")


def send_compound_email(customer_email, download_token):
    """Email 3: The Compound Effect (sent 7 days after purchase)."""
    download_url = f"{config.BASE_URL}/download/{download_token}"

    html = f"""
    <div style="max-width:600px;margin:0 auto;font-family:Arial,Helvetica,sans-serif;background:#FAF6ED;padding:40px 24px;">
      <div style="text-align:center;margin-bottom:32px;">
        <div style="font-size:11px;font-weight:600;letter-spacing:3px;text-transform:uppercase;color:#7B4FBF;">Kingdom Builders AI</div>
      </div>

      <div style="padding:0 8px;">
        <h1 style="font-family:Georgia,serif;font-size:24px;color:#1A0A2E;margin:0 0 20px;">The compound effect (7 days in)</h1>

        <p style="font-size:15px;color:#3A2A55;line-height:1.8;margin:0 0 20px;">
          You've been conducting for a week. Here's what typically happens at this point — and what to focus on next.
        </p>

        <div style="background:linear-gradient(135deg,#1A0A2E 0%,#2D1B4E 100%);border-radius:8px;padding:32px;margin:24px 0;">
          <p style="font-family:Georgia,serif;font-size:18px;color:#FFFFFF;line-height:1.6;font-style:italic;margin:0;">
            "Most people overestimate what they can do in a day and underestimate what they can do in a week of conducting."
          </p>
        </div>

        <p style="font-size:15px;color:#3A2A55;line-height:1.8;margin:0 0 16px;">
          <strong>If your convergence rate is dropping</strong> — from 6-8 rounds down to 3-4 — you're on track. The specification muscle is building. Keep going.
        </p>

        <p style="font-size:15px;color:#3A2A55;line-height:1.8;margin:0 0 16px;">
          <strong>If you're still reverting to old habits</strong> — catching yourself typing long prompts and editing walls of text — revisit Model 01 (The Conductor Model) and specifically the Review-Over-Create Mindset. The identity shift is the foundation. Everything else builds on it.
        </p>

        <p style="font-size:15px;color:#3A2A55;line-height:1.8;margin:0 0 16px;">
          <strong>Your next unlock:</strong> Try the Negative Space Protocol (Model 03) on your hardest problem this week. The one you've been putting off. Use the three cuts — Graveyard, Physics, Blade Test — to eliminate 95% of the noise before you even open your AI tool. What's left is the answer.
        </p>

        <div style="text-align:center;margin-top:24px;">
          <a href="{download_url}" style="display:inline-block;padding:14px 36px;background:linear-gradient(135deg,#D4A843 0%,#E8C96A 100%);color:#1A0A2E;font-size:15px;font-weight:700;text-decoration:none;border-radius:4px;">
            RE-DOWNLOAD THE PLAYBOOK
          </a>
        </div>
      </div>

      <div style="text-align:center;margin-top:32px;font-size:12px;color:#6B5A8A;">
        <p>Questions? Reply to this email or contact support@kingdombuilders.ai</p>
        <p style="margin-top:8px;font-size:11px;color:rgba(107,90,138,0.3);">
          You're receiving this because you purchased The Conductor's Playbook.<br>
          <a href="mailto:support@kingdombuilders.ai?subject=Unsubscribe" style="color:rgba(107,90,138,0.4);">Unsubscribe from follow-up emails</a>
        </p>
      </div>
    </div>
    """

    try:
        result = resend.Emails.send({
            "from": FROM_EMAIL,
            "to": customer_email,
            "subject": "The compound effect (7 days in)",
            "html": html,
        })
        purchase = get_purchase_by_token(download_token)
        if purchase:
            log_email(purchase["id"], "compound", result.get("id") if isinstance(result, dict) else None)
    except Exception as e:
        print(f"Failed to send compound email to {customer_email}: {e}")
