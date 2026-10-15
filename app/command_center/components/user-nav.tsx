'use client';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu';
import { UserAvatarProfile } from '@/components/user-avatar-profile';
import { AHOS_OPERATOR } from '@/lib/operator';
import { useRouter } from 'next/navigation';

/**
 * AHOS: the template showed the Clerk user here. AHOS has one local operator
 * (lib/operator); the menu keeps the same affordances without a remote account.
 */
export function UserNav() {
  const router = useRouter();
  const user = AHOS_OPERATOR;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger render={<Button variant='ghost' className='relative h-8 w-8 rounded-full' />}>
        <UserAvatarProfile user={user} />
      </DropdownMenuTrigger>
      <DropdownMenuContent className='w-56' align='end' sideOffset={10}>
        <DropdownMenuGroup>
          <DropdownMenuLabel className='font-normal'>
            <div className='flex flex-col space-y-1'>
              <p className='text-sm leading-none font-medium'>{user.fullName}</p>
              <p className='text-muted-foreground text-xs leading-none'>{user.role}</p>
            </div>
          </DropdownMenuLabel>
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuGroup>
          <DropdownMenuItem onClick={() => router.push('/settings')}>Settings</DropdownMenuItem>
          <DropdownMenuItem onClick={() => router.push('/audit')}>Audit &amp; Governance</DropdownMenuItem>
          <DropdownMenuItem onClick={() => router.push('/evidence')}>Evidence</DropdownMenuItem>
        </DropdownMenuGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
