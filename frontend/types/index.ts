export interface User {
  id: number
  username: string
  email: string
  role: 'user' | 'moderator' | 'admin' | 'superadmin'
  is_banned: boolean
  storage_used: number
  storage_limit: number
  storage_remaining: number
  storage_usage_percent: number
  created_at: string
}

export interface Repo {
  id: number
  name: string
  slug: string
  description: string | null
  is_public: boolean
  verification_status: 'unverified' | 'pending' | 'verified' | 'rejected'
  download_count: number
  clone_count: number
  file_count: number
  total_size: number
  owner: { id: number; username: string; role: string; created_at: string }
  created_at: string
  updated_at: string
}

export interface RepoFile {
  id: number
  original_name: string
  directory_path: string
  stored_name: string
  mime_type: string
  detected_type: string
  size_bytes: number
  download_count: number
  uploaded_at: string
}

export interface Ad {
  id: number
  title: string
  image_url: string
  target_url: string
  position: string
  description: string | null
  is_active: boolean
  click_count: number
  created_at: string
}

export interface AdminStats {
  total_users: number
  total_repos: number
  total_files: number
  total_storage_bytes: number
  pending_verifications: number
  banned_users: number
}

export interface AdminPermissions {
  manage_users: boolean
  manage_repos: boolean
  manage_ads: boolean
  view_stats: boolean
}

export interface AdminAccount {
  id: number
  username: string
  email: string
  role: 'admin' | 'superadmin'
  created_at: string
  permissions: AdminPermissions
}

export interface AdminAnalytics {
  totals: {
    users: number
    repos: number
    files: number
    storage_bytes: number
    downloads: number
  }
  growth: {
    users_7d: number
    repos_7d: number
    files_7d: number
    users_current_7d: number
    repos_current_7d: number
    files_current_7d: number
  }
  timeline: Array<{ day: string; users: number; repos: number; files: number }>
}


export interface AdminUserMessage {
  id: number
  title: string
  body: string
  is_active: boolean
  created_by: number | null
  recipient_user_id: number | null
  recipient_username: string | null
  created_at: string
  updated_at: string
  acknowledged_users: number
  pending_users: number
}
