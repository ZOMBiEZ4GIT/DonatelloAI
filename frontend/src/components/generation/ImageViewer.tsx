import { useState } from 'react';
import { Download, Maximize2, X } from 'lucide-react';
import { Generation } from '@/types';
import { useDownloadImage } from '@/hooks';
import { formatDateTime } from '@/utils';

interface ImageViewerProps {
  generation: Generation;
}

export const ImageViewer = ({ generation }: ImageViewerProps) => {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const { download, isDownloading } = useDownloadImage();

  if (!generation.image_url) {
    return null;
  }

  return (
    <>
      <div className="group relative aspect-square overflow-hidden bg-gray-100">
        <img
          src={generation.thumbnail_url || generation.image_url}
          alt={generation.prompt}
          className="h-full w-full object-cover transition-transform group-hover:scale-105"
        />
        <div className="absolute inset-0 bg-black/0 transition-colors group-hover:bg-black/40">
          <div className="flex h-full items-center justify-center gap-2 opacity-0 transition-opacity group-hover:opacity-100">
            <button
              onClick={() => setIsFullscreen(true)}
              className="rounded-lg bg-white p-2 text-gray-900 transition-colors hover:bg-gray-100"
              aria-label="View fullscreen"
            >
              <Maximize2 size={20} />
            </button>
            <button
              onClick={() => download(generation)}
              disabled={isDownloading}
              className="rounded-lg bg-white p-2 text-gray-900 transition-colors hover:bg-gray-100 disabled:opacity-50"
              aria-label="Download image"
            >
              <Download size={20} />
            </button>
          </div>
        </div>
      </div>

      {isFullscreen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-4"
          onClick={() => setIsFullscreen(false)}
        >
          <button
            onClick={() => setIsFullscreen(false)}
            className="absolute right-4 top-4 rounded-lg bg-white/10 p-2 text-white transition-colors hover:bg-white/20"
          >
            <X size={24} />
          </button>
          <div className="max-h-full max-w-full" onClick={(e) => e.stopPropagation()}>
            <img
              src={generation.image_url}
              alt={generation.prompt}
              className="max-h-[90vh] max-w-full rounded-lg"
            />
            <div className="mt-4 rounded-lg bg-white/10 p-4 text-white backdrop-blur">
              <p className="mb-2 text-sm">{generation.prompt}</p>
              <p className="text-xs text-gray-300">
                Generated {formatDateTime(generation.created_at)} using {generation.model_used}
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
