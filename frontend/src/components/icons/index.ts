/**
 * Centralized icon exports from Heroicons
 * All icons used in the application should be exported from this file
 * for consistency and easy maintenance.
 *
 * Using outline icons by default for a cleaner, modern look.
 * Solid icons can be imported separately when needed.
 */

// Navigation & UI
export {
  HomeIcon,
  UserGroupIcon,
  BookOpenIcon,
  CloudArrowUpIcon,
  MegaphoneIcon,
  Bars3Icon,
  ChevronRightIcon,
  ChevronLeftIcon,
  PlusIcon,
  MagnifyingGlassIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';

// Actions & Status
export {
  CheckCircleIcon,
  CheckIcon,
  ExclamationCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  XCircleIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';

// Communication & Commerce
export {
  EnvelopeIcon,
  ShoppingBagIcon,
} from '@heroicons/react/24/outline';

// Solid variants for specific use cases
export {
  CheckCircleIcon as CheckCircleIconSolid,
  ExclamationCircleIcon as ExclamationCircleIconSolid,
  InformationCircleIcon as InformationCircleIconSolid,
  XCircleIcon as XCircleIconSolid,
} from '@heroicons/react/24/solid';
