import { useRouteError, isRouteErrorResponse, Link } from 'react-router-dom';
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { Button } from '@/components/ui';

export const RouteErrorBoundary: React.FC = () => {
  const error = useRouteError();

  let errorMessage: string;
  let errorStatus: number | undefined;

  if (isRouteErrorResponse(error)) {
    errorMessage = error.statusText || error.data?.message || 'An error occurred';
    errorStatus = error.status;
  } else if (error instanceof Error) {
    errorMessage = error.message;
  } else {
    errorMessage = 'An unknown error occurred';
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full mb-4">
          <ExclamationTriangleIcon className="w-6 h-6 text-red-600" />
        </div>

        <h1 className="text-2xl font-bold text-center text-gray-900 mb-2">
          {errorStatus ? `Error ${errorStatus}` : 'Something went wrong'}
        </h1>

        <p className="text-gray-600 text-center mb-6">
          {errorMessage}
        </p>

        {error instanceof Error && (
          <details className="mb-6 bg-gray-50 rounded p-4">
            <summary className="cursor-pointer font-medium text-sm text-gray-700 mb-2">
              Error details
            </summary>
            <pre className="text-xs text-red-600 overflow-auto whitespace-pre-wrap break-words">
              {error.stack}
            </pre>
          </details>
        )}

        <div className="flex gap-3">
          <Button
            onClick={() => window.location.reload()}
            variant="secondary"
            className="flex-1"
          >
            Reload Page
          </Button>
          <Link to="/" className="flex-1">
            <Button variant="primary" className="w-full">
              Go Home
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
};
