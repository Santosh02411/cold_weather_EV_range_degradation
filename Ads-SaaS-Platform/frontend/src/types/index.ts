// User types
export interface User {
  id: string
  email: string
  created_at?: string
  updated_at?: string
}

// Platform types
export interface Platform {
  id: string
  name: string
  type: 'facebook' | 'google' | 'tiktok' | 'instagram'
  config: Record<string, any>
  user_id: string
  is_connected: boolean
  created_at: string
  updated_at: string
}

export interface PlatformCredentials {
  facebook?: {
    accessToken: string
    accountId: string
  }
  google?: {
    clientId: string
    clientSecret: string
    refreshToken: string
    developerToken: string
  }
  tiktok?: {
    accessToken: string
    appId: string
  }
  instagram?: {
    accessToken: string
    businessAccountId: string
  }
}

// Campaign types
export interface Campaign {
  id: string
  title: string
  description?: string
  budget: number
  status: 'draft' | 'active' | 'paused' | 'completed'
  schedule_start?: string
  schedule_end?: string
  user_id: string
  created_at: string
  updated_at: string
  platforms?: CampaignPlatform[]
}

export interface CampaignPlatform {
  id: string
  platform_id: string
  platformName: string
  platformType: string
  status: 'pending' | 'success' | 'failed' | 'retrying'
  errorMessage?: string
  retryCount: number
}

export interface CreateCampaignData {
  title: string
  description?: string
  budget: number
  platforms: string[]
  scheduleStart?: string
  scheduleEnd?: string
  objective?: string
}

export interface UpdateCampaignData {
  title?: string
  description?: string
  budget?: number
  status?: string
  scheduleStart?: string
  scheduleEnd?: string
}

// Media types
export interface Media {
  id: string
  filename: string
  original_name: string
  mime_type: string
  size: number
  url: string
  user_id: string
  created_at: string
  updated_at: string
}

export interface CampaignMedia {
  id: string
  campaign_id: string
  media_id: string
  media_type: 'image' | 'video' | 'text'
  ad_copy?: string
  created_at: string
  filename: string
  original_name: string
  mime_type: string
  size: number
  url: string
}

// Job types
export interface Job {
  id: string
  campaign_id: string
  platform_id: string
  action: 'publish' | 'update' | 'delete'
  status: 'pending' | 'processing' | 'success' | 'failed'
  error_message?: string
  retry_count: number
  scheduled_at: string
  processed_at?: string
  created_at: string
  updated_at: string
  campaign_title?: string
  platform_name?: string
}

// Log types
export interface Log {
  id: string
  level: 'info' | 'warn' | 'error' | 'debug'
  message: string
  context: Record<string, any>
  user_id?: string
  campaign_id?: string
  platform_id?: string
  created_at: string
}

// Status types
export interface StatusOverview {
  campaigns: {
    total_campaigns: number
    active_campaigns: number
    draft_campaigns: number
    paused_campaigns: number
    completed_campaigns: number
    total_budget: number
  }
  platforms: {
    total_platforms: number
    connected_platforms: number
    disconnected_platforms: number
  }
  jobs: {
    total_jobs: number
    pending_jobs: number
    processing_jobs: number
    success_jobs: number
    failed_jobs: number
  }
  recentActivity: Log[]
}

export interface CampaignStatus {
  campaign: Campaign
  platformStatus: CampaignPlatform[]
  jobHistory: Job[]
  recentLogs: Log[]
}

export interface PlatformStatus {
  platform: Platform
  campaignPerformance: {
    id: string
    title: string
    campaign_status: string
    platform_status: string
    error_message?: string
    retry_count: number
    created_at: string
  }[]
  recentLogs: Log[]
}

// UI types
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  limit: number
  hasMore: boolean
}

// Form types
export interface FormData {
  [key: string]: any
}

export interface FormErrors {
  [key: string]: string | undefined
}

// Chart types
export interface ChartData {
  name: string
  value: number
  color?: string
}

export interface TimeSeriesData {
  date: string
  value: number
  label?: string
}

// Component props
export interface BaseComponentProps {
  className?: string
  children?: React.ReactNode
}

export interface ModalProps extends BaseComponentProps {
  isOpen: boolean
  onClose: () => void
  title?: string
}

export interface ButtonProps extends BaseComponentProps {
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger' | 'outline'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
  onClick?: () => void
  type?: 'button' | 'submit' | 'reset'
}

export interface InputProps extends BaseComponentProps {
  type?: string
  placeholder?: string
  value?: string
  onChange?: (value: string) => void
  error?: string
  disabled?: boolean
  required?: boolean
}

export interface SelectProps extends BaseComponentProps {
  options: { value: string; label: string }[]
  value?: string
  onChange?: (value: string) => void
  placeholder?: string
  error?: string
  disabled?: boolean
}

export interface TableProps extends BaseComponentProps {
  columns: {
    key: string
    label: string
    render?: (value: any, row: any) => React.ReactNode
  }[]
  data: any[]
  loading?: boolean
  empty?: string
}

// Navigation types
export interface NavItem {
  name: string
  href: string
  icon?: React.ComponentType<any>
  current?: boolean
}

export interface SidebarProps extends BaseComponentProps {
  navigation: NavItem[]
  user?: User
}

// Filter and search types
export interface FilterOptions {
  status?: string
  platform?: string
  dateRange?: string
  search?: string
}

export interface SortOptions {
  field: string
  direction: 'asc' | 'desc'
}

// Notification types
export interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message: string
  timestamp: string
  read: boolean
}
