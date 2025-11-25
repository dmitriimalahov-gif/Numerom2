import React, { useMemo } from 'react';
import DocViewer, { DocViewerRenderers } from '@cyntler/react-doc-viewer';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { X, Download, FileText } from 'lucide-react';
import '@cyntler/react-doc-viewer/dist/index.css';

const SUPPORTED_TYPES = new Set(
  DocViewerRenderers.flatMap((renderer) => renderer.fileTypes || [])
);

const getFileType = (resource) => {
  if (!resource) return 'application/octet-stream';
  const { contentType, file_extension: extFromApi, filename } = resource;
  if (contentType) {
    return contentType;
  }
  const ext = (extFromApi || filename || '').toLowerCase();
  if (ext.endsWith('.pdf')) return 'application/pdf';
  if (ext.endsWith('.docx')) return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
  if (ext.endsWith('.doc')) return 'application/msword';
  if (ext.endsWith('.xlsx')) return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
  if (ext.endsWith('.xls')) return 'application/vnd.ms-excel';
  if (ext.endsWith('.csv')) return 'text/csv';
  if (ext.endsWith('.pptx')) return 'application/vnd.openxmlformats-officedocument.presentationml.presentation';
  if (ext.endsWith('.ppt')) return 'application/vnd.ms-powerpoint';
  if (ext.endsWith('.txt')) return 'text/plain';
  if (ext.endsWith('.rtf')) return 'application/rtf';
  return 'application/octet-stream';
};

const LessonDocumentViewer = ({ resource, backendUrl, onClose }) => {
  if (!resource) return null;

  const {
    title,
    filename,
    resource_url: resourceUrl,
    url,
    contentType,
  } = resource;

  const fullUrl = useMemo(() => {
    const rawUrl = resourceUrl || url || '';
    if (!rawUrl) return null;
    if (rawUrl.startsWith('http://') || rawUrl.startsWith('https://')) {
      return rawUrl;
    }
    return `${backendUrl}${rawUrl}`;
  }, [backendUrl, resourceUrl, url]);

  const documentTitle = title || filename || 'Документ';
  const fileType = getFileType(resource);
  const docViewerType = fileType.split('/').pop();
  const docName = filename || `${documentTitle}.${docViewerType}`;

  const isSupported = useMemo(() => {
    if (!fileType) return false;
    if (SUPPORTED_TYPES.has(fileType)) return true;
    const extension = (filename || '').split('.').pop();
    if (extension && SUPPORTED_TYPES.has(`.${extension.toLowerCase()}`)) {
      return true;
    }
    return false;
  }, [fileType, filename]);

  const documents = useMemo(() => {
    if (!fullUrl) return [];
    return [
      {
        uri: fullUrl,
        fileName: docName,
        fileType,
      },
    ];
  }, [fullUrl, docName, fileType]);

  const handleDownload = () => {
    if (!fullUrl) return;
    const link = document.createElement('a');
    link.href = `${fullUrl}?download=1`;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.click();
  };

  return (
    <div className="fixed inset-0 z-[999] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <Card className="w-full max-w-6xl h-[90vh] flex flex-col overflow-hidden shadow-2xl">
        <CardHeader className="flex-shrink-0 flex items-center justify-between border-b bg-white/70 backdrop-blur-md">
          <CardTitle className="flex items-center gap-2 text-xl font-semibold text-gray-900">
            <span className="inline-flex items-center justify-center w-9 h-9 rounded-full bg-gradient-to-br from-purple-600 to-blue-500 text-white shadow">
              <FileText className="w-5 h-5" />
            </span>
            {documentTitle}
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              className="flex items-center gap-2 border-purple-200 text-purple-700 hover:bg-purple-50"
              onClick={handleDownload}
            >
              <Download className="w-4 h-4" />
              Скачать
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="text-gray-500 hover:text-gray-900"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="flex-1 overflow-hidden p-0 bg-gray-50">
          {fullUrl ? (
            <div className="w-full h-full">
              {isSupported ? (
                <DocViewer
                  documents={documents}
                  pluginRenderers={DocViewerRenderers}
                  theme={{
                    primary: '#6d28d9',
                    textPrimary: '#1f2937',
                  }}
                  config={{
                    header: {
                      disableHeader: true,
                      disableFileName: true,
                    },
                    pdfVerticalScrollByDefault: true,
                  }}
                  className="w-full h-full"
                />
              ) : (
                <div className="w-full h-full flex flex-col items-center justify-center text-center px-6">
                  <div className="w-16 h-16 rounded-full bg-orange-100 flex items-center justify-center mb-4">
                    <FileText className="w-8 h-8 text-orange-500" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Формат файла не поддерживается для предпросмотра</h3>
                  <p className="text-sm text-gray-600 max-w-md mb-4">
                    Вы можете скачать файл и открыть его на устройстве: {docName}
                  </p>
                  <Button
                    onClick={handleDownload}
                    className="bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-700 hover:to-blue-600 text-white"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Скачать файл
                  </Button>
                </div>
              )}
            </div>
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <p className="text-sm text-gray-600">Не удалось определить ссылку на файл</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default LessonDocumentViewer;
