import { Search as SearchIcon } from 'lucide-react'
import { Input } from '@/components/ui/input'

interface SearchProps extends React.InputHTMLAttributes<HTMLInputElement> {
  placeholder?: string
}

export function Search({ placeholder = 'Search...', ...props }: SearchProps) {
  return (
    <div className='relative w-full'>
      <SearchIcon className='absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground' />
      <Input
        type='search'
        placeholder={placeholder}
        className='w-full bg-background pl-8 md:w-[300px] lg:w-[336px]'
        {...props}
      />
    </div>
  )
}