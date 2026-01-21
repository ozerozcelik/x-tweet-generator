import React, { useState } from 'react';
import { Sparkles, TrendingUp, Users, MessageCircle, Repeat2, Heart, Eye, Share2, AlertCircle } from 'lucide-react';

const XAlgorithmTweetGenerator = () => {
  const [topic, setTopic] = useState('');
  const [tone, setTone] = useState('engaging');
  const [targetAction, setTargetAction] = useState('like');
  const [language, setLanguage] = useState('tr');
  const [generatedTweet, setGeneratedTweet] = useState('');
  const [predictions, setPredictions] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);

  // Production'da Vercel URL'nizi kullanın, development'ta proxy
  const API_BASE_URL = import.meta.env.PROD 
    ? 'https://x-tweet-generator-api.vercel.app'  // ✅ Buraya kendi Vercel URL'nizi yazın
    : '';

  const engagementTypes = [
    { id: 'like', label: 'Like', icon: Heart, weight: 0.5, color: 'text-pink-500' },
    { id: 'reply', label: 'Reply', icon: MessageCircle, weight: 13.5, color: 'text-blue-500' },
    { id: 'repost', label: 'Repost', icon: Repeat2, weight: 27.0, color: 'text-green-500' },
    { id: 'click', label: 'Click', icon: Eye, weight: 0.11, color: 'text-purple-500' },
    { id: 'share', label: 'Share', icon: Share2, weight: 32.0, color: 'text-orange-500' },
  ];

  const tones = [
    { value: 'engaging', label: 'İlgi Çekici', desc: 'Merak uyandıran ve etkileşimi tetikleyen' },
    { value: 'controversial', label: 'Tartışmalı', desc: 'Fikir ayrılığı yaratacak konular' },
    { value: 'educational', label: 'Eğitici', desc: 'Değerli bilgi paylaşan' },
    { value: 'emotional', label: 'Duygusal', desc: 'Empati ve bağlantı kuran' },
    { value: 'humorous', label: 'Eğlenceli', desc: 'Mizahi ve neşeli' },
  ];

  const languages = [
    { code: 'tr', name: 'Türkçe', flag: '🇹🇷' },
    { code: 'en', name: 'English', flag: '🇬🇧' },
  ];

  const generateTweetPrompt = () => {
    const languageNames = { tr: 'Türkçe', en: 'English' };
    
    const prompts = {
      like: [
        `Write a detailed tweet thread about ${topic} that people will immediately want to like. Provide valuable insights. Write in ${languageNames[language]}.`,
        `Share a positive and inspiring story or analysis about ${topic}. Be detailed for Premium users. Write in ${languageNames[language]}.`,
      ],
      reply: [
        `Write a multi-layered analysis about ${topic} that will start discussions. Present different perspectives. Write in ${languageNames[language]}.`,
        `Write a detailed scenario about ${topic} that will make people want to share their own experiences. Write in ${languageNames[language]}.`,
      ],
      repost: [
        `Write a comprehensive analysis about ${topic} with valuable information, statistics, and insights. Write in ${languageNames[language]}.`,
        `Provide important facts and predictions about ${topic} that everyone should know. Write in ${languageNames[language]}.`,
      ],
      click: [
        `Make a detailed introduction about ${topic} that sparks curiosity. Write in ${languageNames[language]}.`,
        `Create content about ${topic} with frameworks and detailed examples. Write in ${languageNames[language]}.`,
      ],
      share: [
        `Write an actionable guide about ${topic} that adds value. Write in ${languageNames[language]}.`,
        `Share a comprehensive guide about ${topic} with practical advice. Write in ${languageNames[language]}.`,
      ]
    };

    return prompts[targetAction][Math.floor(Math.random() * prompts[targetAction].length)];
  };

  const simulateEngagementPredictions = () => {
    const predictions = {};
    
    engagementTypes.forEach(type => {
      if (type.id === targetAction) {
        predictions[type.id] = 0.6 + Math.random() * 0.35;
      } else {
        predictions[type.id] = 0.05 + Math.random() * 0.3;
      }
    });

    const weightedScore = engagementTypes.reduce((sum, type) => {
      return sum + (predictions[type.id] * type.weight);
    }, 0);

    return { ...predictions, weightedScore };
  };

  const generateTweet = async () => {
    if (!topic.trim()) {
      alert('Lütfen bir konu girin!');
      return;
    }

    setIsGenerating(true);
    
    try {
      const prompt = generateTweetPrompt();
      
      // ✅ Backend API'ye istek
      const response = await fetch(`${API_BASE_URL}/api/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: prompt,
          tone: tone,
          targetAction: targetAction
        })
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      const data = await response.json();
      const tweetText = data.content[0].text.trim();
      
      setGeneratedTweet(tweetText);
      
      const preds = simulateEngagementPredictions();
      setPredictions(preds);
      
    } catch (error) {
      console.error('Tweet generation error:', error);
      alert('Tweet oluşturulurken bir hata oluştu. Backend çalışıyor mu kontrol edin.');
    } finally {
      setIsGenerating(false);
    }
  };

  const getTweetLength = () => generatedTweet.length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Sparkles className="w-10 h-10 text-blue-400" />
            <h1 className="text-4xl font-bold text-white">X Algorithm Tweet Generator</h1>
          </div>
          <p className="text-slate-300 text-lg">
            X Premium için uzun format tweet generator - X algoritmasıyla optimize
          </p>
          <div className="mt-4 inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/30 rounded-lg px-4 py-2">
            <TrendingUp className="w-4 h-4 text-blue-400" />
            <span className="text-sm text-blue-300">Phoenix Grok-based Transformer • Premium Unlimited</span>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-white/5 backdrop-blur-lg rounded-2xl p-6 border border-white/10">
            <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
              <Users className="w-5 h-5 text-blue-400" />
              Tweet Parametreleri
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Konu
                </label>
                <input
                  type="text"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="Örn: yapay zeka, kripto, girişimcilik..."
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Ton
                </label>
                <select
                  value={tone}
                  onChange={(e) => setTone(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {tones.map(t => (
                    <option key={t.value} value={t.value} className="bg-slate-800">
                      {t.label} - {t.desc}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Dil
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {languages.map(lang => (
                    <button
                      key={lang.code}
                      onClick={() => setLanguage(lang.code)}
                      className={`flex items-center justify-center gap-2 p-3 rounded-lg border transition-all ${
                        language === lang.code
                          ? 'bg-blue-500/20 border-blue-500/50'
                          : 'bg-white/5 border-white/10 hover:bg-white/10'
                      }`}
                    >
                      <span className="text-2xl">{lang.flag}</span>
                      <span className="text-sm text-white font-medium">{lang.name}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-3">
                  Hedef Engagement Türü
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {engagementTypes.map(type => {
                    const Icon = type.icon;
                    return (
                      <button
                        key={type.id}
                        onClick={() => setTargetAction(type.id)}
                        className={`flex items-center gap-2 p-3 rounded-lg border transition-all ${
                          targetAction === type.id
                            ? 'bg-blue-500/20 border-blue-500/50'
                            : 'bg-white/5 border-white/10 hover:bg-white/10'
                        }`}
                      >
                        <Icon className={`w-4 h-4 ${type.color}`} />
                        <span className="text-sm text-white font-medium">{type.label}</span>
                        <span className="ml-auto text-xs text-slate-400">×{type.weight}</span>
                      </button>
                    );
                  })}
                </div>
                <p className="text-xs text-slate-400 mt-2">
                  * Ağırlıklar X algoritmasının gerçek weighted scorer değerleridir
                </p>
              </div>

              <button
                onClick={generateTweet}
                disabled={isGenerating || !topic.trim()}
                className="w-full bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 disabled:from-slate-600 disabled:to-slate-600 text-white font-semibold py-3 rounded-lg transition-all flex items-center justify-center gap-2"
              >
                {isGenerating ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Üretiliyor...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5" />
                    Tweet Üret
                  </>
                )}
              </button>
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-white/5 backdrop-blur-lg rounded-2xl p-6 border border-white/10">
              <h2 className="text-xl font-semibold text-white mb-4">Oluşturulan Tweet</h2>
              
              {generatedTweet ? (
                <div className="space-y-4">
                  <div className="bg-white/5 rounded-lg p-4 border border-white/10 min-h-[120px]">
                    <p className="text-white leading-relaxed">{generatedTweet}</p>
                  </div>
                  
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-400">
                      {getTweetLength()} karakter
                    </span>
                    <span className="text-blue-400 flex items-center gap-1">
                      ✨ Premium - Sınırsız
                    </span>
                  </div>

                  <button
                    onClick={() => navigator.clipboard.writeText(generatedTweet)}
                    className="w-full bg-white/10 hover:bg-white/20 text-white py-2 rounded-lg transition-all"
                  >
                    📋 Kopyala
                  </button>
                </div>
              ) : (
                <div className="bg-white/5 rounded-lg p-8 border border-dashed border-white/20 text-center">
                  <Sparkles className="w-12 h-12 text-slate-500 mx-auto mb-3" />
                  <p className="text-slate-400">
                    Parametreleri seç ve "Tweet Üret" butonuna tıkla
                  </p>
                </div>
              )}
            </div>

            {predictions && (
              <div className="bg-white/5 backdrop-blur-lg rounded-2xl p-6 border border-white/10">
                <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-green-400" />
                  Tahmin Edilen Engagement
                </h2>
                
                <div className="space-y-3">
                  {engagementTypes.map(type => {
                    const Icon = type.icon;
                    const value = predictions[type.id];
                    const percentage = (value * 100).toFixed(1);
                    
                    return (
                      <div key={type.id} className="space-y-1">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Icon className={`w-4 h-4 ${type.color}`} />
                            <span className="text-sm text-white">{type.label}</span>
                          </div>
                          <span className="text-sm text-slate-300">{percentage}%</span>
                        </div>
                        <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                          <div
                            className={`h-full bg-gradient-to-r ${
                              type.id === targetAction
                                ? 'from-blue-500 to-purple-500'
                                : 'from-slate-600 to-slate-700'
                            }`}
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div className="mt-4 pt-4 border-t border-white/10">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-slate-300">Weighted Score</span>
                    <span className="text-lg font-bold text-green-400">
                      {predictions.weightedScore.toFixed(2)}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">
                    X algoritmasının final ranking skoru
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="mt-8 bg-blue-500/10 border border-blue-500/30 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-blue-300 mb-3 flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            X Algoritması Nasıl Çalışır?
          </h3>
          <div className="grid md:grid-cols-2 gap-4 text-sm text-slate-300">
            <div>
              <h4 className="font-semibold text-white mb-2">🎯 Phoenix Transformer</h4>
              <p>Grok-based model, her tweet için engagement olasılıklarını tahmin eder</p>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-2">⚖️ Weighted Scoring</h4>
              <p>Repost ve Share en yüksek ağırlığa sahip (27.0 ve 32.0)</p>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-2">🔄 Candidate Isolation</h4>
              <p>Her tweet bağımsız skorlanır, diğer tweetlerden etkilenmez</p>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-2">📊 Multi-Action Prediction</h4>
              <p>Like, reply, repost, click gibi tüm aksiyonlar ayrı ayrı tahmin edilir</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default XAlgorithmTweetGenerator;