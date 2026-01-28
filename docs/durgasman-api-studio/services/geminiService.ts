
import { GoogleGenAI, Type, Modality } from "@google/genai";
import { ChatMessage, ApiRequest, HttpMethod, Collection, ApiResponse } from "../types";

const getAI = () => new GoogleGenAI({ apiKey: process.env.API_KEY });

export async function chatWithGemini(
  prompt: string, 
  history: ChatMessage[], 
  options: { thinking?: boolean; search?: boolean } = {}
) {
  const ai = getAI();
  const modelName = options.thinking ? 'gemini-3-pro-preview' : 'gemini-3-flash-preview';
  
  const config: any = {
    systemInstruction: "You are Durgasman AI Assistant, an expert in APIs, networking, and software development. Provide concise and accurate technical help.",
  };

  if (options.thinking) {
    config.thinkingConfig = { thinkingBudget: 32768 };
  }

  if (options.search) {
    config.tools = [{ googleSearch: {} }];
  }

  const chat = ai.chats.create({
    model: modelName,
    config
  });

  const response = await chat.sendMessage({ message: prompt });
  
  const groundingUrls = response.candidates?.[0]?.groundingMetadata?.groundingChunks
    ?.map((chunk: any) => chunk.web?.uri)
    .filter(Boolean);

  return {
    text: response.text || "No response generated.",
    groundingUrls
  };
}

export async function analyzeApiResponse(response: ApiResponse, request: ApiRequest): Promise<string> {
  const ai = getAI();
  const prompt = `Analyze this API response.
  Request: ${request.method} ${request.url}
  Response Status: ${response.status} ${response.statusText}
  Response Body: ${JSON.stringify(response.data || response.error)}
  
  Explain what this response means, identify potential issues, and suggest next steps or fixes if needed.`;

  const result = await ai.models.generateContent({
    model: 'gemini-3-flash-preview',
    contents: prompt,
    config: {
      systemInstruction: "You are a senior backend engineer and API expert. Provide a concise, professional analysis of API responses. Use markdown formatting.",
    }
  });

  return result.text || "Failed to analyze response.";
}

export async function generateCollectionDocs(collection: Collection): Promise<string> {
  const ai = getAI();
  const prompt = `Generate professional technical documentation for the following API collection named "${collection.name}". 
  Requests included: ${JSON.stringify(collection.requests.map(r => ({ name: r.name, method: r.method, url: r.url })))}.
  Provide a markdown summary, detailed endpoint breakdowns, and authentication requirements.`;

  const response = await ai.models.generateContent({
    model: 'gemini-3-flash-preview',
    contents: prompt,
    config: {
      systemInstruction: "You are an expert Technical Writer. Generate clean, well-formatted Markdown documentation.",
    }
  });

  return response.text || "Failed to generate documentation.";
}

export async function generateRequestFromPrompt(prompt: string, schemaHint?: string): Promise<Partial<ApiRequest> | null> {
  const ai = getAI();
  const contents = `Generate a valid JSON object for a web API request based on this description: "${prompt}". 
    ${schemaHint ? `Additionally, the user expects the response to follow these requirements: "${schemaHint}".` : ''}
    Response MUST be a single JSON object.`;

  const response = await ai.models.generateContent({
    model: 'gemini-3-flash-preview',
    contents,
    config: {
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.OBJECT,
        properties: {
          name: { type: Type.STRING },
          method: { type: Type.STRING },
          url: { type: Type.STRING },
          params: { type: Type.ARRAY, items: { type: Type.OBJECT, properties: { key: {type: Type.STRING}, value: {type: Type.STRING}, enabled: {type: Type.BOOLEAN} } } },
          headers: { type: Type.ARRAY, items: { type: Type.OBJECT, properties: { key: {type: Type.STRING}, value: {type: Type.STRING}, enabled: {type: Type.BOOLEAN} } } },
          body: { type: Type.STRING },
          responseSchema: { type: Type.STRING }
        }
      }
    }
  });

  try {
    const data = JSON.parse(response.text);
    return {
      ...data,
      id: Math.random().toString(36).substring(7),
      params: (data.params || []).map((p: any) => ({ ...p, id: Math.random().toString(36).substring(7) })),
      headers: (data.headers || []).map((h: any) => ({ ...h, id: Math.random().toString(36).substring(7) })),
    };
  } catch (e) {
    return null;
  }
}

export async function generateImage(prompt: string, aspectRatio: string = "1:1", imageSize: string = "1K") {
  const ai = getAI();
  const response = await ai.models.generateContent({
    model: 'gemini-3-pro-image-preview',
    contents: { parts: [{ text: prompt }] },
    config: { imageConfig: { aspectRatio: aspectRatio as any, imageSize: imageSize as any } },
  });
  for (const part of response.candidates[0].content.parts) {
    if (part.inlineData) return `data:image/png;base64,${part.inlineData.data}`;
  }
  return null;
}

export async function speak(text: string) {
  const ai = getAI();
  const response = await ai.models.generateContent({
    model: "gemini-2.5-flash-preview-tts",
    contents: [{ parts: [{ text }] }],
    config: {
      responseModalities: [Modality.AUDIO],
      speechConfig: { voiceConfig: { prebuiltVoiceConfig: { voiceName: 'Kore' } } },
    },
  });
  const base64Audio = response.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
  if (!base64Audio) return;
  const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 });
  const audioBuffer = await decodeAudioData(decode(base64Audio), audioContext, 24000, 1);
  const source = audioContext.createBufferSource();
  source.buffer = audioBuffer;
  source.connect(audioContext.destination);
  source.start();
}

export function decode(base64: string) {
  const binaryString = atob(base64);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) bytes[i] = binaryString.charCodeAt(i);
  return bytes;
}

export function encode(bytes: Uint8Array) {
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i]);
  return btoa(binary);
}

export async function decodeAudioData(data: Uint8Array, ctx: AudioContext, sampleRate: number, numChannels: number): Promise<AudioBuffer> {
  const dataInt16 = new Int16Array(data.buffer);
  const frameCount = dataInt16.length / numChannels;
  const buffer = ctx.createBuffer(numChannels, frameCount, sampleRate);
  for (let channel = 0; channel < numChannels; channel++) {
    const channelData = buffer.getChannelData(channel);
    for (let i = 0; i < frameCount; i++) channelData[i] = dataInt16[i * numChannels + channel] / 32768.0;
  }
  return buffer;
}

export function createPcmBlob(data: Float32Array): { data: string, mimeType: string } {
  const l = data.length;
  const int16 = new Int16Array(l);
  for (let i = 0; i < l; i++) int16[i] = data[i] * 32768;
  return { data: encode(new Uint8Array(int16.buffer)), mimeType: 'audio/pcm;rate=16000' };
}

export const connectLive = (callbacks: any) => {
    const ai = getAI();
    return ai.live.connect({
        model: 'gemini-2.5-flash-native-audio-preview-12-2025',
        callbacks,
        config: {
            responseModalities: [Modality.AUDIO],
            speechConfig: { voiceConfig: { prebuiltVoiceConfig: { voiceName: 'Zephyr' } } },
            systemInstruction: 'You are Durgasman AI Live Assistant. Help users debug their API requests in real-time.',
        }
    });
};
