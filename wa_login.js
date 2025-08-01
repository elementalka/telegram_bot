const { Client, LocalAuth } = require('whatsapp-web.js');

const sessionPath = process.argv[2] || 'wa_session';

const client = new Client({
    authStrategy: new LocalAuth({ dataPath: sessionPath }),
    puppeteer: { headless: true }
});

client.on('qr', qr => {
    console.log('QR:' + qr);
});

client.on('ready', () => {
    console.log('READY');
    setTimeout(() => process.exit(0), 1000);
});

client.on('auth_failure', msg => {
    console.log('AUTH_FAIL:' + msg);
    process.exit(1);
});

client.initialize();
