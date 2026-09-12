/**
 * Wix Velo Backend Web Module
 * Yönetim panelinin ENCORE Flask API'sinden güvenli şekilde
 * lead kayıtlarını almasını sağlar.
 *
 * Gerçek ADMIN_API_KEY bu dosyada tutulmaz.
 * Anahtar Wix Secrets Manager'daki ENCORE_ADMIN_API_KEY
 * kaydından okunur.
 */

import { webMethod, Permissions } from 'wix-web-module';
import { fetch } from 'wix-fetch';
import { getSecret } from 'wix-secrets-backend';

const API_URL =
  'https://encore-ai-smartlead.onrender.com/api/leads';

export const getLeads = webMethod(
  Permissions.Anyone,

  async () => {
    const adminKey = await getSecret(
      'ENCORE_ADMIN_API_KEY'
    );

    const response = await fetch(API_URL, {
      method: 'get',
      headers: {
        'Content-Type': 'application/json',
        'X-Admin-Key': adminKey
      }
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
      throw new Error(
        data.error || 'Lead kayıtları alınamadı.'
      );
    }

    return data;
  }
);
