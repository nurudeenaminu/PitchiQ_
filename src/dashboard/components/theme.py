"""Theme configuration and styling for PitchIQ dashboard."""
import streamlit as st

THEME = {
  "accent": "#3ddc97",
  "cyan": "#4cc9f0",
  "amber": "#f4a261",
  "rose": "#ef476f",
  "muted": "#7a93a6",
  "surface": "#0f1f2e",
  "card": "#132738",
  "border": "#26445f",
  "bg": "#07131f",
  "text": "#d5e4ef",
}


def apply_theme() -> None:
    """Apply blueprint-aligned dark theme with typography system."""
    st.markdown(
        f"""
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;700;800&family=Space+Grotesk:wght@500;700&display=swap');
          @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css');

          :root {{
            --bg: {THEME["bg"]};
            --surface: {THEME["surface"]};
            --card: {THEME["card"]};
            --border: {THEME["border"]};
            --text: {THEME["text"]};
            --muted: {THEME["muted"]};
            --accent: {THEME["accent"]};
            --cyan: {THEME["cyan"]};
            --amber: {THEME["amber"]};
            --rose: {THEME["rose"]};
          }}

          .stApp {{
            background:
              radial-gradient(900px 500px at 10% -20%, #1e3d55 0%, transparent 65%),
              radial-gradient(700px 420px at 90% -10%, #1f6f5f 0%, transparent 65%),
              var(--bg);
            color: var(--text);
            font-family: "Manrope", sans-serif;
          }}

          .main .block-container {{
            padding-top: 1.5rem;
          }}

          h1, h2, h3 {{
            font-family: "Space Grotesk", sans-serif !important;
            letter-spacing: -0.01em;
            color: #e8f2f9;
          }}

          .stTabs [data-baseweb="tab-list"] {{
            gap: 0.45rem;
          }}

          .stTabs [data-baseweb="tab"] {{
            background: rgba(19, 39, 56, 0.72);
            border: 1px solid rgba(74, 119, 154, 0.45);
            border-radius: 999px;
            padding: 8px 16px;
            font-family: "Space Grotesk", sans-serif;
            font-size: 0.86rem;
          }}

          .stTabs [aria-selected="true"] {{
            background: linear-gradient(135deg, rgba(61, 220, 151, 0.2), rgba(76, 201, 240, 0.18));
            border-color: rgba(61, 220, 151, 0.75);
          }}

          .ticker {{
            border: 1px solid rgba(74, 119, 154, 0.42);
            background: linear-gradient(135deg, rgba(19, 39, 56, 0.85), rgba(15, 31, 46, 0.72));
            border-radius: 14px;
            padding: 10px 12px;
            color: var(--cyan);
            font-size: 13px;
            font-weight: 600;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            box-shadow: 0 10px 24px rgba(6, 15, 24, 0.28);
            animation: card-in 0.4s ease both;
          }}

          .hero {{
            border: 1px solid rgba(103, 151, 191, 0.5);
            background:
              radial-gradient(circle at 0% 0%, rgba(76, 201, 240, 0.25), transparent 45%),
              radial-gradient(circle at 100% 100%, rgba(61, 220, 151, 0.2), transparent 45%),
              linear-gradient(135deg, rgba(19, 39, 56, 0.86), rgba(9, 20, 31, 0.95));
            border-radius: 18px;
            padding: 24px 22px;
            box-shadow: 0 18px 44px rgba(3, 10, 18, 0.35);
            animation: card-in 0.45s ease both;
          }}

          .hero-title {{
            color: #f0fffa;
            font-size: clamp(30px, 5vw, 48px);
            font-weight: 800;
            line-height: 0.98;
            margin-bottom: 10px;
          }}

          .hero-sub {{
            color: #bfd5e4;
            font-size: 0.95rem;
            margin-bottom: 14px;
          }}

          .hero-badges {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
          }}

          .hero-badge {{
            background: rgba(8, 19, 29, 0.6);
            border: 1px solid rgba(76, 201, 240, 0.45);
            color: #dff3ff;
            border-radius: 999px;
            padding: 6px 11px;
            font-size: 0.78rem;
            display: inline-flex;
            align-items: center;
            gap: 7px;
          }}

          .soft {{
            color: var(--muted);
            font-size: 12px;
            letter-spacing: 0.02em;
          }}

          .card {{
            background: linear-gradient(145deg, rgba(19, 39, 56, 0.9), rgba(14, 30, 45, 0.78));
            border: 1px solid rgba(90, 136, 170, 0.45);
            border-radius: 14px;
            padding: 14px 15px;
            box-shadow: 0 8px 24px rgba(6, 16, 25, 0.25);
            animation: card-in 0.45s ease both;
          }}

          .kpi-label {{
            color: #9eb5c7;
            font-size: 0.77rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 6px;
            display: inline-flex;
            gap: 8px;
            align-items: center;
          }}

          .kpi-value {{
            font-family: "Space Grotesk", sans-serif;
            font-size: 1.58rem;
            margin: 0;
          }}

          .match-row {{
            border: 1px solid rgba(75, 118, 150, 0.4);
            background: rgba(9, 21, 33, 0.72);
            border-radius: 12px;
            padding: 8px 12px;
            margin-bottom: 8px;
          }}

          @keyframes card-in {{
            from {{
              opacity: 0;
              transform: translateY(8px);
            }}
            to {{
              opacity: 1;
              transform: translateY(0);
            }}
          }}

          .error-box {{
            border: 1px solid var(--rose);
            background: rgba(239, 71, 111, 0.14);
            border-radius: 10px;
            padding: 12px;
            color: var(--rose);
            font-size: 12px;
          }}

          .success-box {{
            border: 1px solid var(--accent);
            background: rgba(61, 220, 151, 0.12);
            border-radius: 10px;
            padding: 12px;
            color: var(--accent);
            font-size: 12px;
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )
