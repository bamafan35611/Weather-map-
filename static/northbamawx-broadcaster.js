/**
 * NorthBamaWX 15-Minute Broadcast Scheduler
 * Drop-in solution for automated weather broadcasting
 */

class NorthBamaWXBroadcaster {
    constructor(config = {}) {
        this.baseUrl = config.baseUrl || 'https://weather-map-zfln.onrender.com';
        this.localArea = config.localArea || 'North Alabama';
        this.enabled = config.enabled !== false;
        this.debug = config.debug || false;
        
        this.log('✅ NorthBamaWX Broadcaster initialized');
    }
    
    log(message) {
        if (this.debug) {
            console.log(`[NorthBamaWX] ${message}`);
        }
    }
    
    /**
     * Main broadcast function - call this every minute
     */
    async checkAndBroadcast() {
        if (!this.enabled) return;
        
        const now = new Date();
        const minute = now.getMinutes();
        
        // Only broadcast on :00, :15, :30, :45
        if (minute % 15 !== 0) {
            return;
        }
        
        this.log(`🎙️ Broadcast time! Current: ${now.toLocaleTimeString()}`);
        
        try {
            const response = await fetch(`${this.baseUrl}/api/broadcast/scheduled?local_area=${encodeURIComponent(this.localArea)}`);
            const data = await response.json();
            
            if (!data.success) {
                console.error('Broadcast error:', data.error);
                return;
            }
            
            if (data.broadcast_type === 'none') {
                this.log(data.message);
                return;
            }
            
            this.log(`📻 Broadcasting: ${data.broadcast_type}`);
            this.log(`📊 Alert count: ${data.alert_count}`);
            
            // Speak all content items
            for (const item of data.content) {
                await this.speakItem(item);
            }
            
        } catch (error) {
            console.error('Broadcast failed:', error);
        }
    }
    
    /**
     * Speak a single content item
     */
    async speakItem(item) {
        this.log(`🗣️ Speaking ${item.type}: ${item.text.substring(0, 50)}...`);
        
        // Call your TTS function here
        await this.speak(item.text, item.voice_style);
        
        // Pause between items
        if (item.type !== 'quiet') {
            await this.sleep(2000);
        }
    }
    
    /**
     * YOUR TTS INTEGRATION GOES HERE
     * Replace this with your actual text-to-speech system
     */
    async speak(text, voiceStyle = 'calm') {
        console.log(`🗣️ [${voiceStyle.toUpperCase()}] ${text}`);
        
        // TODO: Replace with your actual TTS
        // Examples:
        
        // Browser TTS:
        // const utterance = new SpeechSynthesisUtterance(text);
        // utterance.rate = voiceStyle === 'emergency' ? 1.2 : 1.0;
        // utterance.pitch = voiceStyle === 'emergency' ? 1.1 : 1.0;
        // speechSynthesis.speak(utterance);
        
        // Azure TTS:
        // await azureTTS.speak(text, voiceStyle);
        
        // OBS Browser Source:
        // window.obsstudio?.speak(text);
        
        // For now, just log it
        await this.sleep(1000);
    }
    
    /**
     * Helper: sleep for ms milliseconds
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    /**
     * Start the broadcast scheduler
     */
    start() {
        this.log('🚀 Starting 15-minute broadcast scheduler...');
        
        // Check immediately
        this.checkAndBroadcast();
        
        // Then check every minute
        this.interval = setInterval(() => {
            this.checkAndBroadcast();
        }, 60000); // 60 seconds
        
        this.log('✅ Scheduler started! Broadcasting at :00, :15, :30, :45');
    }
    
    /**
     * Stop the broadcast scheduler
     */
    stop() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
            this.log('🛑 Scheduler stopped');
        }
    }
    
    /**
     * Manually trigger a broadcast (for testing)
     */
    async broadcastNow() {
        this.log('🎙️ Manual broadcast triggered');
        await this.checkAndBroadcast();
    }
}

// ============================================
// USAGE EXAMPLES
// ============================================

// Example 1: Basic usage
const broadcaster = new NorthBamaWXBroadcaster({
    baseUrl: 'https://weather-map-zfln.onrender.com',
    localArea: 'North Alabama',
    debug: true
});

broadcaster.start();

// Example 2: With custom TTS integration
class MyCustomBroadcaster extends NorthBamaWXBroadcaster {
    async speak(text, voiceStyle) {
        // Your custom TTS code here
        console.log(`Speaking with ${voiceStyle} voice: ${text}`);
        
        // Example: Browser TTS
        const utterance = new SpeechSynthesisUtterance(text);
        
        // Adjust voice based on style
        switch(voiceStyle) {
            case 'emergency':
                utterance.rate = 1.3;
                utterance.pitch = 1.2;
                utterance.volume = 1.0;
                break;
            case 'urgent':
                utterance.rate = 1.15;
                utterance.pitch = 1.1;
                utterance.volume = 0.9;
                break;
            case 'concerned':
                utterance.rate = 1.05;
                utterance.pitch = 1.05;
                utterance.volume = 0.8;
                break;
            default: // calm
                utterance.rate = 1.0;
                utterance.pitch = 1.0;
                utterance.volume = 0.8;
        }
        
        speechSynthesis.speak(utterance);
        
        // Wait for speech to finish
        await new Promise(resolve => {
            utterance.onend = resolve;
        });
    }
}

// Example 3: Test broadcast immediately
// broadcaster.broadcastNow();

// Example 4: Stop broadcasts
// broadcaster.stop();

// ============================================
// EXPORT (if using modules)
// ============================================
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NorthBamaWXBroadcaster;
}
