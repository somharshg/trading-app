import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://vcvatxteaengpvxwvltt.supabase.co'
const supabaseKey = 'sb_publishable_-GK7zXTMhjNu_8GHvYyswQ_YmlMhr5j'

export const supabase = createClient(supabaseUrl, supabaseKey)