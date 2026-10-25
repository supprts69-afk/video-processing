// frontend/lib/supabaseClient.ts
import { createClient } from '@supabase/supabase-js'

// ফলব্যাক হিসেবে ডামি স্ট্রিং দেওয়া হলো, যাতে বিল্ডের সময় ক্র্যাশ না করে
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://placeholder.supabase.co'
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'placeholder'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
