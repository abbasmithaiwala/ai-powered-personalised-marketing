import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { getErrorMessage } from '@/api/client'

interface UseApiMutationOptions<TData, TVariables> {
  mutationFn: (variables: TVariables) => Promise<TData>
  onSuccess?: (data: TData, variables: TVariables) => void
  onError?: (error: Error, variables: TVariables) => void
  successMessage?: string
  errorMessage?: string
}

export function useApiMutation<TData = unknown, TVariables = unknown>({
  mutationFn,
  onSuccess,
  onError,
  successMessage,
  errorMessage,
}: UseApiMutationOptions<TData, TVariables>) {
  return useMutation({
    mutationFn,
    onSuccess: (data, variables) => {
      if (successMessage) {
        toast.success(successMessage)
      }
      onSuccess?.(data, variables)
    },
    onError: (error: Error, variables) => {
      const message = errorMessage || getErrorMessage(error)
      toast.error(message)
      onError?.(error, variables)
    },
  })
}
