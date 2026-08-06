const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require('@whiskeysockets/baileys');
const pino = require('pino');
const express = require('express');
const TelegramBot = require('node-telegram-bot-api');

// -------------------------------------------------------------
// ১. এখানে রেন্ডারের Environment Variable থেকে টোকেন অটো নিয়ে নেবে।
// আপনার কোডের ভেতরে আর আলাদা করে টোকেন বসানোর কোনো দরকার নেই।
// রেন্ডারের Environment Variables-এ 'TELEGRAM_BOT_TOKEN' নামে টোকেন দিলেই হবে।
// -------------------------------------------------------------
const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN;

if (!TELEGRAM_BOT_TOKEN) {
    console.error("❌ Error: TELEGRAM_BOT_TOKEN environment variable is missing in Render!");
}

const app = express();
app.use(express.json());

// টেলিগ্রাম বট ইনিশিয়ালাইজ (Polling মোড)
const bot = new TelegramBot(TELEGRAM_BOT_TOKEN, { polling: true });

let sock;
let qrCodeData = 'Connecting... Please wait for WhatsApp connection.';

async function connectToWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState('./auth_info_baileys');

    sock = makeWASocket({
        auth: state,
        printQRInTerminal: true,
        logger: pino({ level: 'silent' })
    });

    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect, qr } = update;
        if (qr) {
            qrCodeData = qr;
            console.log('QR Received. Please scan or check web logs.');
        }
        if (connection === 'close') {
            const shouldReconnect = (lastDisconnect?.error)?.output?.statusCode !== DisconnectReason.loggedOut;
            console.log('Connection closed, reconnecting...', shouldReconnect);
            if (shouldReconnect) {
                connectToWhatsApp();
            }
        } else if (connection === 'open') {
            console.log('✅ WhatsApp Connected Successfully for Telegram Bot!');
            qrCodeData = 'Connected Successfully!';
        }
    });

    sock.ev.on('creds.update', saveCreds);
}

connectToWhatsApp();

// টেলিগ্রাম বটের মেসেজ হ্যান্ডলার
bot.on('message', async (msg) => {
    const chatId = msg.chat.id;
    const text = msg.text ? msg.text.trim() : '';

    if (text === '/start') {
        return bot.sendMessage(chatId, "👋 স্বাগতম! যেকোনো হোয়াটসঅ্যাপ নাম্বার (যেমন: 88017XXXXXXXX) পাঠান, আমি চেক করে বলে দেব অ্যাকাউন্ট খোলা আছে কি না।");
    }

    const phoneNumber = text.replace(/[^0-9]/g, '');

    if (phoneNumber.length < 8) {
        return bot.sendMessage(chatId, "❌ দয়া করে একটি সঠিক ফোন নাম্বার পাঠান (কান্ট্রি কোড সহ)।");
    }

    if (!sock || !sock.onWhatsApp) {
        return bot.sendMessage(chatId, "⚠️ হোয়াটসঅ্যাপ এখনো কানেক্ট হয়নি। একটু পরে আবার চেষ্টা করুন।");
    }

    try {
        bot.sendMessage(chatId, `🔍 চেক করা হচ্ছে: ${phoneNumber}...`);

        const formattedJid = phoneNumber + '@s.whatsapp.net';
        const [result] = await sock.onWhatsApp(formattedJid);

        if (result && result.exists) {
            bot.sendMessage(chatId, `✅ **Result:**\n\n📌 নাম্বার: \`${phoneNumber}\`\n💬 স্ট্যাটাস: **এই নাম্বারে হোয়াটসঅ্যাপ অ্যাকাউন্ট খোলা আছে!**`, { parse_mode: 'Markdown' });
        } else {
            bot.sendMessage(chatId, `❌ **Result:**\n\n📌 নাম্বার: \`${phoneNumber}\`\n💬 স্ট্যাটাস: **এই নাম্বারে কোনো হোয়াটসঅ্যাপ অ্যাকাউন্ট নেই।**`, { parse_mode: 'Markdown' });
        }
    } catch (error) {
        bot.sendMessage(chatId, `⚠️ এরর হয়েছে: ${error.message}`);
    }
});

// রেন্ডার সার্ভারের জন্য সাধারণ একটি রাউট
app.get('/', (req, res) => {
    res.send(`Telegram WhatsApp Checker Bot is Running! Status: ${qrCodeData}`);
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
