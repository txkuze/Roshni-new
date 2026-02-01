# -*- coding: utf-8 -*-
"""
Passive technology & CMS detection
"""

import requests
from urllib.parse import urlparse

COMMON_CMS = {
    "WordPress": ["/wp-login.php", "/wp-admin/", "wp-content"],
    "Joomla": ["/administrator/", "joomla"],
    "Drupal": ["/user/login", "drupal"],
    "Magento": ["/admin", "mage/"],
    "Laravel": [".env", "laravel"],
    "Shopify": ["cdn.shopify.com", "myshopify.com"],
}


def fingerprint_cms(url: str) -> list:
    """
    Passive CMS / tech detection
    Returns list of CMS/frameworks detected
    """
    detected = []
    try:
        response = requests.get(url, timeout=6, headers={"User-Agent": "Passive-VL-Scanner"})
        html = response.text.lower()
        path = urlparse(url).path.lower()

        for cms, signatures in COMMON_CMS.items():
            for sig in signatures:
                if sig.lower() in html or sig.lower() in path:
                    detected.append(cms)
                    break  # Only report once per CMS

    except Exception:
        pass

    return list(set(detected))
