from pyrogram import Client, filters
from pyrogram.types import Message
import subprocess
import os
import re
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime
import asyncio

def ultimate_format_report(domain, risk_level, score, threats, recommendations, os_guess="", traceroute="", vulns=[]):
    """Advanced report formatter"""
    report = f"""🚨 ULTIMATE NMAP DEEP SCAN - {domain.upper()}
{'═' * 60}
🔍 TARGET INFO
Domain/IP: {domain}
Risk Level: {risk_level} | Score: {score}/100
🖥️  OS DETECTION: {os_guess or 'Unknown'}
📊 PORT SCAN RESULTS (TCP/UDP)"""
    for threat in threats[:15]:
        report += f"• {threat}"
        
    if vulns:
        report += f"🎯 KNOWN VULNERABILITIES:"for vuln in vulns[:10]:
            report += f"• {vuln}"
    
    if traceroute:
        report += f"
🗺️  TRACEROUTE:
{traceroute[:500]}
"report += f"🛡️ CRITICAL RECOMMENDATIONS:"
    for rec in recommendations:
        report += f"• {rec}"    
    report += f"{'═' * 60}
⏱️  Scan completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    return report

def parse_ultimate_nmap(xml_path, domain):
    """Parse comprehensive Nmap XML with ALL techniques"""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # TCP Ports
        tcp_open = []
        udp_open = []
        services = []
        vulns = []
        os_guess = "Unknown"
        traceroute = []
        
        # TCP ports
        for port in root.findall('.//port[state/@state="open"]'):
            portid = port.get('portid')
            protocol = port.find('protocol').text if port.find('protocol') is not None else 'tcp'
            service = port.find('service')
            service_name = service.get('name', 'unknown') if service else 'unknown'
            version = service.get('version', '') if service else ''
            
            port_info = f"{portid}/{protocol} ({service_name}"
            if version:
                port_info += f" {version}"
            port_info += ")"
            
            if protocol == 'tcp':
                tcp_open.append(port_info)
                services.append(f"{service_name}:{portid}")
            else:
                udp_open.append(port_info)
        
        # OS Detection
        for os in root.findall('.//osmatch'):
            os_guess = f"{os.get('name', 'Unknown')} {os.get('accuracy', '')}%"
            break
        
        # Vulnerabilities/Scripts
        for script in root.findall('.//script'):
            if 'vuln' in script.get('id', '').lower() or script.get('id') in ['vulners']:
                output = script.find('output')
                if output is not None and output.text:
                    vulns.append(f"{script.get('id', 'vuln')} - {output.text.strip()[:100]}")
        
        # Traceroute
        for hop in root.findall('.//hop'):
            traceroute.append(f"{hop.get('ttl')} → {hop.get('ipaddr')}")
        
        all_ports = tcp_open + udp_open
        threats = all_ports or ["No open ports detected ✓"]
        
        if services:
            threats.append(f"Services: {', '.join(services[:8])}")
        
        score = max(95 - len(all_ports) * 7 - len(vulns) * 5, 10)
        risk = "CRITICAL" if score < 40 else "HIGH" if score < 60 else "MEDIUM" if score < 80 else "LOW"
        
        return {
            "domain": domain,
            "risk": risk,
            "score": score,
            "threats": threats,
            "recommendations": [
                "🚨 IMMEDIATELY close unnecessary ports",
                f"Update {', '.join(services[:3])} services",
                "Run: nmap -sC -sV --script=vulners -A {domain}",
                "Enable firewall/WAF protection",
                "Disable unused services",
                "Change default credentials",
                "Monitor logs for exploit attempts"
            ],
            "os_guess": os_guess,
            "traceroute": " → ".join(traceroute[-5:]) if traceroute else "",
            "vulns": vulns
        }
    except:
        return {
            "domain": domain, "risk": "ERROR", "score": 0,
            "threats": ["XML parsing failed"], 
            "recommendations": ["Check nmap installation"],
            "os_guess": "", "traceroute": "", "vulns": []
        }

@Client.on_message(filters.command("nmap", prefixes="/") & (filters.private | filters.group))
async def ultimate_nmap_handler(client: Client, message: Message):
    """ULTIMATE NMAP - ALL techniques in ONE scan"""
    
    if len(message.command) < 2:
        await message.reply(
            "🔥 **ULTIMATE NMAP SCANNER**"
            "**Usage:** `/nmap example.com`"
            "**Scans:** TCP/UDP ports + OS detection + Vulns + Traceroute + Services"
            "**Time:** ~60-120s (DEEP scan)"
        )
        return

    target = re.sub(r'^(https?://)?(www.)?', '', message.command[1]).strip('/')
    if not re.match(r'^[a-zA-Z0-9.-]+$', target):
        await message.reply("❌ Invalid target!")
        return

    status_msg = await message.reply(f"🚀 **ULTIMATE SCAN STARTED** `{target}`⏳ This takes 60-120s...")
    
    xml_path = None
    try:
        # ULTIMATE NMAP COMMAND - ALL FEATURES
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as tmp:
            xml_path = tmp.name

        cmd = [
            "nmap",
            # CORE SCANNING
            "-sS", "-sU", "--top-ports", "1000",  # SYN + UDP top 1000
            "-sV", "--version-intensity", "9",    # Aggressive service detection
            "-O",                                 # OS Detection
            "--traceroute",                       # Network path
            # VULNERABILITY SCANNING
            "--script", "vuln,vulners,smb-vuln*,http-vuln*",
            "--script-args", "vulners.showdescription",
            # PERFORMANCE
            "-T4", "--host-timeout", "60s", "--max-retries", "2",
            # OUTPUT
            "-oX", xml_path,
            target
        ]
        
        await status_msg.edit_text(f"🔍 **Executing:** `nmap {' '.join(cmd[3:])} {target}`")
        
        # Run with 2min timeout
        proc = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None, lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            ), 130.0
        )
        
        if proc.returncode != 0:
            await status_msg.edit_text(f"❌ **Nmap failed:**```{proc.stderr[:800]}```")
            return

        # Parse ULTIMATE results
        result = parse_ultimate_nmap(xml_path, target)
        text_report = ultimate_format_report(**result)

        # FINAL RESULTS
        await status_msg.edit_text(
            f"✅ **ULTIMATE SCAN COMPLETE!** `{target}`"
            f"**Risk:** {result['risk']} | **Score:** {result['score']}/100"
            f"**OS:** {result.get('os_guess', 'Unknown')}"
        )
        
        # Split long report
        for i in range(0, len(text_report), 4000):
            await message.reply(f"```{text_report[i:i+4000]}```")

    except asyncio.TimeoutError:
        await status_msg.edit_text("⏰ **TIMEOUT** (2min max)")
    except Exception as e:
        await status_msg.edit_text(f"❌ **ERROR:** `{str(e)}`")
    finally:
        if xml_path and os.path.exists(xml_path):
            os.unlink(xml_path)

# QUICK SCAN OPTION
@Client.on_message(filters.command("nmapquick", prefixes="/") & (filters.private | filters.group))
async def quick_nmap(client: Client, message: Message):
    """Fast scan (~15s)"""
    if len(message.command) < 2:
        return await message.reply("/nmapquick <target>")
    
    target = message.command[1]
    status = await message.reply(f"⚡ Quick scanning {target}...")
    
    try:
        result = subprocess.run([
            "nmap", "-sV", "--top-ports", "100", target
        ], capture_output=True, text=True, timeout=20)
        
        await status.edit_text(f"```{result.stdout}```")
    except:
        await status.edit_text("Quick scan failed")
