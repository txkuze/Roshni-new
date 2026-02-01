import sys
import os
import threading
import asyncio
import requests
from bs4 import BeautifulSoup
from config import BOT_TOKEN
from urllib.parse import urljoin, urlparse
from fpdf import FPDF

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ================= CONFIG =================

SEC_HEADERS = [
    "X-Frame-Options",
    "Content-Security-Policy",
    "X-XSS-Protection",
    "Strict-Transport-Security",
    "Referrer-Policy",
    "Permissions-Policy",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

COMMON_CMS = {
    "WordPress": ["/wp-login.php", "/wp-admin/", "wp-content"],
    "Joomla": ["/administrator/", "joomla"],
    "Drupal": ["/user/login", "drupal"],
    "Magento": ["/admin", "mage/"],
    "Laravel": [".env", "laravel"],
    "Shopify": ["cdn.shopify.com", "myshopify.com"],
}

sys.setrecursionlimit(3000)

# ==================== HELPERS =====================
def pdf_safe(text, max_len=80):
    if not isinstance(text, str):
        text = str(text)
    text = text[:max_len]
    return text.encode("latin-1", "ignore").decode("latin-1")


def normalize_url(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        return "https://" + url
    return url


def check_ssl(domain: str) -> bool:
    import ssl, socket
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(
            socket.socket(), server_hostname=domain
        ) as s:
            s.settimeout(3)
            s.connect((domain, 443))
        return True
    except:
        return False


def scan_headers(url: str) -> list:
    issues = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=6)
        headers = r.headers
        for h in SEC_HEADERS:
            if h not in headers:
                issues.append(f"{h.upper()} MISSING")
        if "Server" in headers:
            issues.append(f"SERVER HEADER EXPOSED: {headers.get('Server')}")
        if "X-Powered-By" in headers:
            issues.append(f"TECH DISCLOSURE VIA X-POWERED-BY: {headers.get('X-Powered-By')}")
    except:
        issues.append("FAILED TO FETCH HEADERS")
    return issues


def fingerprint_cms(url: str) -> list:
    detected = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=6)
        html = r.text.lower()
        path = urlparse(url).path.lower()
        for cms, sigs in COMMON_CMS.items():
            for sig in sigs:
                if sig.lower() in html or sig.lower() in path:
                    detected.append(cms)
                    break
    except:
        pass
    return list(set(detected))


def scan_website(target: str) -> dict:
    result = {
        "domain": target,
        "ssl": False,
        "threats": [],
        "recommendations": [],
        "score": 10,
        "risk": "LOW",
        "cms": [],
    }

    url = normalize_url(target)
    parsed = urlparse(url)

    # SSL check
    if parsed.scheme == "https":
        result["ssl"] = check_ssl(parsed.hostname)
        if not result["ssl"]:
            result["threats"].append("INVALID OR MISCONFIGURED SSL CERTIFICATE")
            result["recommendations"].append("CONFIGURE VALID SSL/TLS")
            result["score"] -= 2
    else:
        result["threats"].append("WEBSITE DOES NOT ENFORCE HTTPS")
        result["recommendations"].append("ENABLE HTTPS")
        result["score"] -= 3

    # Header scan
    header_issues = scan_headers(url)
    result["threats"].extend(header_issues)
    result["score"] -= len(header_issues)

    # CMS detection
    cms_list = fingerprint_cms(url)
    if cms_list:
        result["cms"] = cms_list
        result["threats"].append(f"DETECTED CMS/TECH: {', '.join(cms_list)}")
        result["recommendations"].append("KEEP CMS & PLUGINS UP-TO-DATE")

    # Risk level
    if result["score"] <= 4:
        result["risk"] = "CRITICAL"
    elif result["score"] <= 6:
        result["risk"] = "HIGH"
    elif result["score"] <= 8:
        result["risk"] = "MEDIUM"

    result["score"] = max(1, result["score"])
    return result


def format_text_report(result: dict) -> str:
    report = (
        f"🛡 WEBSITE SCAN REPORT\n"
        f"▸ DOMAIN : {result['domain']}\n"
        f"▸ RISK LEVEL : {result['risk']}\n"
        f"▸ SCORE : {result['score']}/10\n\n"
        "⟐ IDENTIFIED THREATS ⟐\n"
    )
    for t in result["threats"]:
        report += f"• {t}\n"
    report += "\n⟐ RECOMMENDATIONS ⟐\n"
    for r in result["recommendations"]:
        report += f"➤ {r}\n"
    return report


def make_pdf(results, user_id):
    filename = f"report_{user_id}.pdf"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "WEBSITE SECURITY AUDIT REPORT", ln=True)
    pdf.ln(6)

    pdf.set_font("Arial", "B", 9)
    headers = ["URL", "SSL", "THREATS", "SCORE", "RISK"]
    widths = [70, 15, 70, 15, 20]

    for h, w in zip(headers, widths):
        pdf.cell(w, 7, h, border=1)
    pdf.ln()

    pdf.set_font("Arial", size=8)

    for r in results:
        threats_text = ", ".join(r["threats"])[:70]
        row = [
            pdf_safe(r["domain"]),
            "YES" if r["ssl"] else "NO",
            pdf_safe(threats_text),
            str(r["score"]),
            r["risk"],
        ]
        for item, w in zip(row, widths):
            pdf.cell(w, 6, item, border=1)
        pdf.ln()

    pdf.output(filename)
    return filename


# ================= TELEGRAM =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("🎯 Set Target", callback_data="info")],
        [InlineKeyboardButton("🔍 Start Scan", callback_data="scan")],
        [InlineKeyboardButton("📄 Generate PDF", callback_data="pdf")],
        [InlineKeyboardButton("👨‍💻 ᴅᴇᴠᴇʟᴏᴘᴇʀ", url="https://t.me/cyber_github")],
    ]
    await update.message.reply_text(
        "🛡 ADVANCED WEBSITE SCANNER BOT\n⚠ SCAN ONLY WEBSITES YOU OWN OR HAVE PERMISSION FOR.",
        reply_markup=InlineKeyboardMarkup(kb),
    )


async def vlscan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage:\n/vlscan <website>")
        return

    target = context.args[0].rstrip("/")
    context.user_data.clear()
    context.user_data["target"] = target
    context.user_data["results_ready"] = False

    msg = await update.message.reply_text(f"🔍 STARTING PASSIVE SCAN FOR {target}…")
    loop = asyncio.get_running_loop()

    def run_scan():
        result = scan_website(target)
        context.user_data["results"] = [result]
        context.user_data["results_ready"] = True

        # Send textual report
        text_report = format_text_report(result)
        asyncio.run_coroutine_threadsafe(
            update.message.reply_text(f"```\n{text_report}\n```", parse_mode=None),
            loop,
        )

        # Update progress message
        asyncio.run_coroutine_threadsafe(
            msg.edit_text(
                f"✅ SCAN COMPLETE!\nRISK LEVEL: {result['risk']}\nSCORE: {result['score']}/10"
            ),
            loop,
        )

    threading.Thread(target=run_scan, daemon=True).start()


async def vlpdf_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("results_ready"):
        await update.message.reply_text("❌ Scan not completed yet")
        return

    results = context.user_data.get("results", [])
    if not results:
        await update.message.reply_text("❌ No scan results found")
        return

    filename = make_pdf(results, update.effective_user.id)
    with open(filename, "rb") as doc:
        await update.message.reply_document(doc)
    os.remove(filename)


# ================== RUN BOT ======================
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("vlscan", vlscan_command))
app.add_handler(CommandHandler("vlpdf", vlpdf_command))
app.run_polling()
