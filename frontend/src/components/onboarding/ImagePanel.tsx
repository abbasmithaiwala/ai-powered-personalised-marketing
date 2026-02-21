import { memo } from "react"

interface ImagePanelProps {
  imageUrl: string
  alt: string
}

export const ImagePanel = memo(function ImagePanel({
  imageUrl,
  alt,
}: ImagePanelProps) {
  return (
    <div className="relative w-full h-full bg-gray-100">
      <img
        src={imageUrl}
        alt={alt}
        className="absolute inset-0 w-full h-full object-cover"
      />
      <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent" />
    </div>
  )
})
