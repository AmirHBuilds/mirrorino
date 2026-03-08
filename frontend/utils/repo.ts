export type VerificationStatus = 'unverified' | 'pending' | 'verified' | 'rejected'

export function visibleVerificationStatus(status: VerificationStatus, isOwner: boolean): VerificationStatus {
  if (status === 'pending' && !isOwner) return 'unverified'
  return status
}
