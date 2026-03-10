"""
Email service — port of all 4 email functions from the Flask emails.py.

Uses the Resend API to send transactional emails. HTML templates are
kept inline (matching the original Flask implementation exactly) to
preserve pixel-perfect rendering.
"""

import resend

from api.config import settings

resend.api_key = settings.RESEND_API_KEY

FROM_EMAIL = "The Conductor's Playbook <playbook@kingdombuilders.ai>"
FROM_EMAIL_KB = "Kingdom Builders AI <playbook@kingdombuilders.ai>"


def _base_url() -> str:
    """Return the current BASE_URL from settings (re-read each call so tests can patch it)."""
    return settings.BASE_URL


def _log_email_for_purchase(download_token: str, email_type: str, resend_id: str | None) -> None:
    """Log the sent email against the related purchase record (legacy SQLite)."""
    try:
        from database import get_purchase_by_token, log_email
        purchase = get_purchase_by_token(download_token)
        if purchase:
            log_email(purchase["id"], email_type, resend_id)
    except Exception:
        # In the new PostgreSQL world the legacy database module might not
        # be available.  Swallow silently — the new EmailLog model should
        # be used instead when the full migration is complete.
        pass


# ============================================================================
# Email 1: Immediate delivery with download link
# ============================================================================
def send_delivery_email(customer_email: str, download_token: str) -> None:
    """Send the purchase confirmation with a download button."""
    download_url = f"{_base_url()}/download/{download_token}"

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
        resend_id = result.get("id") if isinstance(result, dict) else None
        _log_email_for_purchase(download_token, "delivery", resend_id)
    except Exception as e:
        print(f"Failed to send delivery email to {customer_email}: {e}")


# ============================================================================
# Email 2: Quick Start Guide (sent 24 hours after purchase)
# ============================================================================
def send_quickstart_email(customer_email: str, download_token: str) -> None:
    """24-hour follow-up with actionable first-session guidance."""
    download_url = f"{_base_url()}/download/{download_token}"

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
        resend_id = result.get("id") if isinstance(result, dict) else None
        _log_email_for_purchase(download_token, "quickstart", resend_id)
    except Exception as e:
        print(f"Failed to send quickstart email to {customer_email}: {e}")


# ============================================================================
# Email 3: The Compound Effect (sent 7 days after purchase)
# ============================================================================
def send_compound_email(customer_email: str, download_token: str) -> None:
    """7-day follow-up with progress check and next-unlock guidance."""
    download_url = f"{_base_url()}/download/{download_token}"

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
        resend_id = result.get("id") if isinstance(result, dict) else None
        _log_email_for_purchase(download_token, "compound", resend_id)
    except Exception as e:
        print(f"Failed to send compound email to {customer_email}: {e}")


# ============================================================================
# Email 4: Free chapter lead magnet
# ============================================================================
def send_password_reset_email(email: str, raw_token: str) -> None:
    """Send a password reset link to the user."""
    reset_url = f"{_base_url()}/reset-password?token={raw_token}"

    html = f"""
    <div style="max-width:600px;margin:0 auto;font-family:Arial,Helvetica,sans-serif;background:#FAF6ED;padding:40px 24px;">
      <div style="text-align:center;margin-bottom:32px;">
        <div style="font-size:11px;font-weight:600;letter-spacing:3px;text-transform:uppercase;color:#7B4FBF;">Kingdom Builders AI</div>
      </div>

      <div style="background:linear-gradient(135deg,#1A0A2E 0%,#2D1B4E 100%);border-radius:8px;padding:40px 32px;text-align:center;">
        <h1 style="font-family:Georgia,serif;font-size:28px;color:#FFFFFF;margin:0 0 8px;">Reset Your Password</h1>
        <p style="font-size:15px;color:rgba(255,255,255,0.5);margin:0 0 32px;">We received a request to reset your password. Click the button below to choose a new one.</p>

        <a href="{reset_url}" style="display:inline-block;padding:16px 48px;background:linear-gradient(135deg,#D4A843 0%,#E8C96A 100%);color:#1A0A2E;font-size:16px;font-weight:700;text-decoration:none;border-radius:4px;">
          RESET PASSWORD
        </a>

        <p style="font-size:13px;color:rgba(255,255,255,0.3);margin-top:24px;">
          This link expires in 1 hour. If you didn't request this, you can safely ignore this email.
        </p>
      </div>

      <div style="text-align:center;margin-top:32px;font-size:12px;color:#6B5A8A;">
        <p>Questions? Reply to this email or contact support@kingdombuilders.ai</p>
      </div>
    </div>
    """

    try:
        resend.Emails.send({
            "from": FROM_EMAIL_KB,
            "to": email,
            "subject": "Reset your password",
            "html": html,
        })
    except Exception as e:
        print(f"Failed to send password reset email to {email}: {e}")


# ============================================================================
# Email 6: Email verification for new registrations
# ============================================================================
def send_verification_email(email: str, raw_token: str) -> None:
    """Send an email verification link to a newly registered user."""
    verify_url = f"{_base_url()}/verify-email?token={raw_token}"

    html = f"""
    <div style="max-width:600px;margin:0 auto;font-family:Arial,Helvetica,sans-serif;background:#FAF6ED;padding:40px 24px;">
      <div style="text-align:center;margin-bottom:32px;">
        <div style="font-size:11px;font-weight:600;letter-spacing:3px;text-transform:uppercase;color:#7B4FBF;">Kingdom Builders AI</div>
      </div>

      <div style="background:linear-gradient(135deg,#1A0A2E 0%,#2D1B4E 100%);border-radius:8px;padding:40px 32px;text-align:center;">
        <h1 style="font-family:Georgia,serif;font-size:28px;color:#FFFFFF;margin:0 0 8px;">Welcome to Kingdom Builders AI</h1>
        <p style="font-size:15px;color:rgba(255,255,255,0.5);margin:0 0 32px;">Please verify your email address to complete your registration.</p>

        <a href="{verify_url}" style="display:inline-block;padding:16px 48px;background:linear-gradient(135deg,#D4A843 0%,#E8C96A 100%);color:#1A0A2E;font-size:16px;font-weight:700;text-decoration:none;border-radius:4px;">
          VERIFY EMAIL
        </a>

        <p style="font-size:13px;color:rgba(255,255,255,0.3);margin-top:24px;">
          This link expires in 24 hours.
        </p>
      </div>

      <div style="text-align:center;margin-top:32px;font-size:12px;color:#6B5A8A;">
        <p>Questions? Reply to this email or contact support@kingdombuilders.ai</p>
      </div>
    </div>
    """

    try:
        resend.Emails.send({
            "from": FROM_EMAIL_KB,
            "to": email,
            "subject": "Verify your email address",
            "html": html,
        })
    except Exception as e:
        print(f"Failed to send verification email to {email}: {e}")


# ============================================================================
# Email 4 (legacy numbering): Free chapter lead magnet
# ============================================================================
def send_lead_magnet_email(email: str) -> None:
    """Send free Chapter 1 of The Salmon Journey to a new subscriber."""
    chapter_url = f"{_base_url()}/free/salmon-journey-ch1"
    playbook_url = f"{_base_url()}/thesalmonjourney"

    html = f"""
    <div style="max-width:600px;margin:0 auto;font-family:Arial,Helvetica,sans-serif;background:#FDFCFA;padding:40px 24px;">
      <div style="text-align:center;margin-bottom:32px;">
        <div style="font-size:11px;font-weight:600;letter-spacing:3px;text-transform:uppercase;color:#0A3A5A;">Kingdom Builders AI</div>
      </div>

      <div style="background:linear-gradient(135deg,#052030 0%,#0A3A5A 100%);border-radius:8px;padding:40px 32px;text-align:center;">
        <div style="font-size:3rem;margin-bottom:12px;">&#x1F41F;</div>
        <h1 style="font-family:Georgia,serif;font-size:24px;color:#FFFFFF;margin:0 0 8px;">Your Free Chapter Is Ready</h1>
        <p style="font-size:14px;color:rgba(255,255,255,0.5);margin:0 0 28px;">The Salmon Journey — Chapter 1: The Two Paths</p>

        <a href="{chapter_url}" style="display:inline-block;padding:16px 48px;background:linear-gradient(135deg,#D4A020 0%,#F0C040 100%);color:#052030;font-size:16px;font-weight:700;text-decoration:none;border-radius:4px;">
          READ CHAPTER 1
        </a>
      </div>

      <div style="padding:32px 0;text-align:center;">
        <p style="font-size:15px;color:#3A4A5A;line-height:1.7;margin-bottom:16px;">
          Meet Steady and Flash — two salmon who teach you how compound interest actually works. One swims 1% farther every day. The other waits for one big sprint. Only one makes it.
        </p>
        <p style="font-size:14px;color:#6A7A8A;line-height:1.6;">
          This is Chapter 1 of 5. If you want the full story — including The Rule of 72, The Dark Side of Compound Interest, and The Millionaire Math — <a href="{playbook_url}" style="color:#D4A020;font-weight:600;">get the full playbook for $14.99</a>.
        </p>
      </div>

      <div style="border-top:1px solid #F2F0E8;padding-top:24px;text-align:center;">
        <p style="font-size:11px;color:#A0A8B0;line-height:1.5;">
          Kingdom Builders AI &middot; <a href="{playbook_url}" style="color:#D4A020;">kingdombuilders.ai</a>
        </p>
      </div>
    </div>
    """

    try:
        resend.Emails.send({
            "from": FROM_EMAIL_KB,
            "to": email,
            "subject": "Your free chapter: The Salmon Journey",
            "html": html,
        })
    except Exception as e:
        print(f"Failed to send lead magnet email to {email}: {e}")


# ============================================================================
# Nurture Email 2: "The Playbook You Didn't Expect" (Day 2)
# ============================================================================
def send_nurture_day2(email: str) -> None:
    """Day 2 nurture: introduce The Narrator playbook (identity/self-story)."""
    narrator_url = f"{_base_url()}/read/the-narrator"

    html = f"""
    <div style="max-width:600px;margin:0 auto;font-family:Arial,Helvetica,sans-serif;background:#FAF6ED;padding:40px 24px;">
      <div style="text-align:center;margin-bottom:32px;">
        <div style="font-size:11px;font-weight:600;letter-spacing:3px;text-transform:uppercase;color:#7B4FBF;">Kingdom Builders AI</div>
      </div>

      <div style="padding:0 8px;">
        <h1 style="font-family:Georgia,serif;font-size:24px;color:#1A0A2E;margin:0 0 20px;">The playbook you didn't expect</h1>

        <p style="font-size:15px;color:#3A2A55;line-height:1.8;margin:0 0 20px;">
          You tell yourself a story about who you are. What if that story is wrong?
        </p>

        <p style="font-size:15px;color:#3A2A55;line-height:1.8;margin:0 0 20px;">
          The Narrator is one of our most personal playbooks. It's not about business strategy or productivity. It's about the voice in your head that decides what things mean before you even finish experiencing them.
        </p>

        <div style="background:#FFFFFF;border-radius:8px;padding:24px;border-left:4px solid #D4A843;margin:24px 0;">
          <p style="font-size:15px;color:#3A2A55;line-height:1.7;margin:0;">
            Every decision you make passes through the filter of a story you wrote years ago. The Narrator shows you how to see that story clearly, question it honestly, and rewrite the parts that no longer serve you.
          </p>
        </div>

        <p style="font-size:15px;color:#3A2A55;line-height:1.8;margin:0 0 24px;">
          It's free. It takes about 10 minutes. And it might change the way you see everything else.
        </p>

        <div style="text-align:center;">
          <a href="{narrator_url}" style="display:inline-block;padding:16px 48px;background:linear-gradient(135deg,#D4A843 0%,#E8C96A 100%);color:#1A0A2E;font-size:16px;font-weight:700;text-decoration:none;border-radius:4px;">
            READ THE NARRATOR (FREE)
          </a>
        </div>
      </div>

      <div style="text-align:center;margin-top:32px;font-size:12px;color:#6B5A8A;">
        <p>Questions? Reply to this email or contact support@kingdombuilders.ai</p>
        <p style="margin-top:8px;font-size:11px;color:rgba(107,90,138,0.3);">
          You're receiving this because you signed up at Kingdom Builders AI.<br>
          <a href="mailto:support@kingdombuilders.ai?subject=Unsubscribe" style="color:rgba(107,90,138,0.4);">Unsubscribe</a>
        </p>
      </div>
    </div>
    """

    try:
        resend.Emails.send({
            "from": FROM_EMAIL_KB,
            "to": email,
            "subject": "The playbook you didn't expect",
            "html": html,
        })
    except Exception as e:
        print(f"Failed to send nurture day 2 email to {email}: {e}")


# ============================================================================
# Nurture Email 3: "Why Animals?" (Day 5)
# ============================================================================
def send_nurture_day5(email: str) -> None:
    """Day 5 nurture: explain the animal parable method, tease The Wolf's Table."""
    wolfs_table_url = f"{_base_url()}/read/the-wolfs-table"

    html = f"""
    <div style="max-width:600px;margin:0 auto;font-family:Arial,Helvetica,sans-serif;background:#FAF6ED;padding:40px 24px;">
      <div style="text-align:center;margin-bottom:32px;">
        <div style="font-size:11px;font-weight:600;letter-spacing:3px;text-transform:uppercase;color:#7B4FBF;">Kingdom Builders AI</div>
      </div>

      <div style="padding:0 8px;">
        <h1 style="font-family:Georgia,serif;font-size:24px;color:#1A0A2E;margin:0 0 20px;">Why we teach through animals</h1>

        <p style="font-size:15px;color:#3A2A55;line-height:1.8;margin:0 0 20px;">
          A salmon doesn't have an ego. A wolf doesn't get defensive. An eagle doesn't argue back.
        </p>

        <p style="font-size:15px;color:#3A2A55;line-height:1.8;margin:0 0 20px;">
          That's the point. When you read about an animal navigating a hard situation, your defenses come down. You absorb the lesson before the part of your brain that resists new ideas even notices what happened.
        </p>

        <div style="background:linear-gradient(135deg,#1A0A2E 0%,#2D1B4E 100%);border-radius:8px;padding:32px;margin:24px 0;">
          <p style="font-family:Georgia,serif;font-size:18px;color:#FFFFFF;line-height:1.6;font-style:italic;margin:0;">
            "People don't resist good ideas. They resist being told they need them."
          </p>
        </div>

        <p style="font-size:15px;color:#3A2A55;line-height:1.8;margin:0 0 20px;">
          We've built 54 playbooks across 14 categories: finance, leadership, AI productivity, negotiation, resilience, identity, and more. Each one uses an animal parable to make complex ideas stick without the usual resistance.
        </p>

        <p style="font-size:15px;color:#3A2A55;line-height:1.8;margin:0 0 24px;">
          Here's a good one to try next: The Wolf's Table. It's a negotiation framework built around how wolves share a kill. Who eats first, who waits, and why the order matters more than the size of the meal.
        </p>

        <div style="text-align:center;">
          <a href="{wolfs_table_url}" style="display:inline-block;padding:16px 48px;background:linear-gradient(135deg,#D4A843 0%,#E8C96A 100%);color:#1A0A2E;font-size:16px;font-weight:700;text-decoration:none;border-radius:4px;">
            READ THE WOLF'S TABLE (FREE)
          </a>
        </div>
      </div>

      <div style="text-align:center;margin-top:32px;font-size:12px;color:#6B5A8A;">
        <p>Questions? Reply to this email or contact support@kingdombuilders.ai</p>
        <p style="margin-top:8px;font-size:11px;color:rgba(107,90,138,0.3);">
          You're receiving this because you signed up at Kingdom Builders AI.<br>
          <a href="mailto:support@kingdombuilders.ai?subject=Unsubscribe" style="color:rgba(107,90,138,0.4);">Unsubscribe</a>
        </p>
      </div>
    </div>
    """

    try:
        resend.Emails.send({
            "from": FROM_EMAIL_KB,
            "to": email,
            "subject": "Why we teach through animals",
            "html": html,
        })
    except Exception as e:
        print(f"Failed to send nurture day 5 email to {email}: {e}")


# ============================================================================
# Nurture Email 4: "The 3 Most Popular" (Day 8)
# ============================================================================
def send_nurture_day8(email: str) -> None:
    """Day 8 nurture: preview 3 popular paid playbooks."""
    base = _base_url()
    eagle_url = f"{base}/theeagleslens"
    bear_url = f"{base}/thebearswinter"
    conductor_url = f"{base}/theconductorsplaybook"
    catalog_url = f"{base}/"

    html = f"""
    <div style="max-width:600px;margin:0 auto;font-family:Arial,Helvetica,sans-serif;background:#FAF6ED;padding:40px 24px;">
      <div style="text-align:center;margin-bottom:32px;">
        <div style="font-size:11px;font-weight:600;letter-spacing:3px;text-transform:uppercase;color:#7B4FBF;">Kingdom Builders AI</div>
      </div>

      <div style="padding:0 8px;">
        <h1 style="font-family:Georgia,serif;font-size:24px;color:#1A0A2E;margin:0 0 20px;">Our 3 most-read playbooks</h1>

        <p style="font-size:15px;color:#3A2A55;line-height:1.8;margin:0 0 24px;">
          You've explored a couple of our free playbooks. Here are the three that readers come back to the most.
        </p>

        <div style="background:#FFFFFF;border-radius:8px;padding:24px;border-left:4px solid #D4A843;margin:0 0 16px;">
          <h3 style="font-family:Georgia,serif;font-size:18px;color:#1A0A2E;margin:0 0 8px;">
            <a href="{eagle_url}" style="color:#1A0A2E;text-decoration:none;">The Eagle's Lens</a>
          </h3>
          <p style="font-size:14px;color:#3A2A55;line-height:1.7;margin:0;">
            How eagles see the whole field before they move. A strategy framework for leaders who keep getting pulled into the weeds.
          </p>
        </div>

        <div style="background:#FFFFFF;border-radius:8px;padding:24px;border-left:4px solid #D4A843;margin:0 0 16px;">
          <h3 style="font-family:Georgia,serif;font-size:18px;color:#1A0A2E;margin:0 0 8px;">
            <a href="{bear_url}" style="color:#1A0A2E;text-decoration:none;">The Bear's Winter</a>
          </h3>
          <p style="font-size:14px;color:#3A2A55;line-height:1.7;margin:0;">
            How bears prepare for hard seasons and emerge stronger. A resilience playbook for anyone walking through a difficult chapter.
          </p>
        </div>

        <div style="background:#FFFFFF;border-radius:8px;padding:24px;border-left:4px solid #D4A843;margin:0 0 24px;">
          <h3 style="font-family:Georgia,serif;font-size:18px;color:#1A0A2E;margin:0 0 8px;">
            <a href="{conductor_url}" style="color:#1A0A2E;text-decoration:none;">The Conductor's Playbook</a>
          </h3>
          <p style="font-size:14px;color:#3A2A55;line-height:1.7;margin:0;">
            Our flagship. How to stop prompting AI and start conducting it. The playbook that turns you from a passenger into a pilot.
          </p>
        </div>

        <div style="text-align:center;">
          <a href="{catalog_url}" style="display:inline-block;padding:16px 48px;background:linear-gradient(135deg,#D4A843 0%,#E8C96A 100%);color:#1A0A2E;font-size:16px;font-weight:700;text-decoration:none;border-radius:4px;">
            BROWSE ALL 54 PLAYBOOKS
          </a>
        </div>
      </div>

      <div style="text-align:center;margin-top:32px;font-size:12px;color:#6B5A8A;">
        <p>Questions? Reply to this email or contact support@kingdombuilders.ai</p>
        <p style="margin-top:8px;font-size:11px;color:rgba(107,90,138,0.3);">
          You're receiving this because you signed up at Kingdom Builders AI.<br>
          <a href="mailto:support@kingdombuilders.ai?subject=Unsubscribe" style="color:rgba(107,90,138,0.4);">Unsubscribe</a>
        </p>
      </div>
    </div>
    """

    try:
        resend.Emails.send({
            "from": FROM_EMAIL_KB,
            "to": email,
            "subject": "Our 3 most-read playbooks",
            "html": html,
        })
    except Exception as e:
        print(f"Failed to send nurture day 8 email to {email}: {e}")


# ============================================================================
# Nurture Email 5: "Unlock Everything" (Day 12)
# ============================================================================
def send_nurture_day12(email: str) -> None:
    """Day 12 nurture: subscription pitch."""
    checkout_url = f"{_base_url()}/checkout-redirect?mode=monthly&slug=all"

    html = f"""
    <div style="max-width:600px;margin:0 auto;font-family:Arial,Helvetica,sans-serif;background:#FAF6ED;padding:40px 24px;">
      <div style="text-align:center;margin-bottom:32px;">
        <div style="font-size:11px;font-weight:600;letter-spacing:3px;text-transform:uppercase;color:#7B4FBF;">Kingdom Builders AI</div>
      </div>

      <div style="padding:0 8px;">
        <h1 style="font-family:Georgia,serif;font-size:24px;color:#1A0A2E;margin:0 0 20px;">One key. 54 playbooks.</h1>

        <p style="font-size:15px;color:#3A2A55;line-height:1.8;margin:0 0 20px;">
          Over the past two weeks, you've read a few of our playbooks. You've seen how animal parables can shift the way you think about money, leadership, negotiation, and identity.
        </p>

        <p style="font-size:15px;color:#3A2A55;line-height:1.8;margin:0 0 20px;">
          The free ones are good. The ones behind the door are the ones people build their businesses around.
        </p>

        <div style="background:linear-gradient(135deg,#1A0A2E 0%,#2D1B4E 100%);border-radius:8px;padding:32px;margin:24px 0;text-align:center;">
          <p style="font-family:Georgia,serif;font-size:20px;color:#FFFFFF;line-height:1.6;margin:0 0 24px;">
            Unlimited access to all 54 playbooks.
          </p>
          <div style="display:inline-block;background:rgba(255,255,255,0.08);border-radius:8px;padding:20px 32px;margin:0 8px 12px;">
            <p style="font-size:14px;color:rgba(255,255,255,0.5);margin:0 0 4px;">Monthly</p>
            <p style="font-family:Georgia,serif;font-size:28px;color:#D4A843;margin:0;">$10<span style="font-size:14px;color:rgba(255,255,255,0.4);">/mo</span></p>
          </div>
          <div style="display:inline-block;background:rgba(255,255,255,0.08);border-radius:8px;padding:20px 32px;margin:0 8px 12px;">
            <p style="font-size:14px;color:rgba(255,255,255,0.5);margin:0 0 4px;">Yearly</p>
            <p style="font-family:Georgia,serif;font-size:28px;color:#D4A843;margin:0;">$100<span style="font-size:14px;color:rgba(255,255,255,0.4);">/yr</span></p>
            <p style="font-size:12px;color:#D4A843;margin:4px 0 0;">Save $20</p>
          </div>
        </div>

        <p style="font-size:15px;color:#3A2A55;line-height:1.8;margin:0 0 24px;">
          Every playbook. Every category. Every new release. One subscription.
        </p>

        <div style="text-align:center;">
          <a href="{checkout_url}" style="display:inline-block;padding:16px 48px;background:linear-gradient(135deg,#D4A843 0%,#E8C96A 100%);color:#1A0A2E;font-size:16px;font-weight:700;text-decoration:none;border-radius:4px;">
            GET UNLIMITED ACCESS
          </a>
        </div>
      </div>

      <div style="text-align:center;margin-top:32px;font-size:12px;color:#6B5A8A;">
        <p>Questions? Reply to this email or contact support@kingdombuilders.ai</p>
        <p style="margin-top:8px;font-size:11px;color:rgba(107,90,138,0.3);">
          You're receiving this because you signed up at Kingdom Builders AI.<br>
          <a href="mailto:support@kingdombuilders.ai?subject=Unsubscribe" style="color:rgba(107,90,138,0.4);">Unsubscribe</a>
        </p>
      </div>
    </div>
    """

    try:
        resend.Emails.send({
            "from": FROM_EMAIL_KB,
            "to": email,
            "subject": "One key. 54 playbooks.",
            "html": html,
        })
    except Exception as e:
        print(f"Failed to send nurture day 12 email to {email}: {e}")
