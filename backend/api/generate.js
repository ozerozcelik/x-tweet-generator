// backend/api/generate.js
import Anthropic from '@anthropic-ai/sdk';

export default async function handler(req, res) {
  // CORS headers - tüm originlere izin ver
  res.setHeader('Access-Control-Allow-Credentials', true);
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
  res.setHeader('Access-Control-Allow-Headers', 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version');

  // OPTIONS request için hemen dön
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  // Sadece POST isteklerine izin ver
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { prompt, tone, targetAction } = req.body;

    // Validation
    if (!prompt) {
      return res.status(400).json({ error: 'Prompt is required' });
    }

    // Anthropic client oluştur
    const anthropic = new Anthropic({
      apiKey: process.env.ANTHROPIC_API_KEY,
    });

    // Claude'dan tweet oluştur
    const message = await anthropic.messages.create({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 1000,
      messages: [
        {
          role: 'user',
          content: `Sen bir X (Twitter) içerik uzmanısın. ${prompt}

Ton: ${tone}

Kurallar:
- X Premium kullanıcısı için uzun format içerik
- ${tone === 'engaging' ? 'Güçlü hook ile başla' : ''}
- ${targetAction === 'reply' ? 'Soru veya tartışma teşvik et' : ''}
- Emoji kullan ama profesyonel kalsın (2-3 tane)
- Hashtag sayısını 3 ile sınırla
- Değer katan, detaylı içerik oluştur
- 500-1000 karakter arası ideal

Sadece tweet metnini döndür, başka açıklama yapma.`
        }
      ]
    });

    // Tweet metnini al
    const tweetText = message.content[0].text.trim();

    // Frontend'in beklediği formatta döndür
    res.status(200).json({
      content: [
        {
          text: tweetText,
          type: 'text'
        }
      ]
    });

  } catch (error) {
    console.error('API Error:', error);
    
    // Hata detaylarını döndür
    res.status(500).json({ 
      error: 'Tweet generation failed', 
      details: error.message,
      type: error.type || 'unknown_error'
    });
  }
}

// Export config for Vercel
export const config = {
  runtime: 'nodejs',
  maxDuration: 30, // 30 saniye timeout
};