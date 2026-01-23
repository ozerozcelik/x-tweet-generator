import createClient from "@/lib/supabase/server"

export const createClientComponentClient = () => {
  return createClient()
}
