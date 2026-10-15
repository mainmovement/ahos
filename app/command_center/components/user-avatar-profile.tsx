import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';

interface UserAvatarProfileProps {
  className?: string;
  showInfo?: boolean;
  /**
   * AHOS: the template passed a Clerk user. We pass the local operator
   * (lib/operator). The shape stays compatible with a plain identity object.
   */
  user: {
    imageUrl?: string;
    fullName?: string | null;
    role?: string | null;
    emailAddresses?: Array<{ emailAddress: string }>;
  } | null;
}

export function UserAvatarProfile({ className, showInfo = false, user }: UserAvatarProfileProps) {
  const subline = user?.role ?? user?.emailAddresses?.[0]?.emailAddress ?? '';
  return (
    <div className='flex items-center gap-2'>
      <Avatar className={className}>
        <AvatarImage src={user?.imageUrl || ''} alt={user?.fullName || ''} />
        <AvatarFallback className='rounded-lg'>
          {user?.fullName?.slice(0, 2)?.toUpperCase() || 'AH'}
        </AvatarFallback>
      </Avatar>

      {showInfo && (
        <div className='grid flex-1 text-left text-sm leading-tight'>
          <span className='truncate font-semibold'>{user?.fullName || ''}</span>
          <span className='truncate text-xs'>{subline}</span>
        </div>
      )}
    </div>
  );
}
