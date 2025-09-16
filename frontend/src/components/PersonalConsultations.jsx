import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Alert, AlertDescription } from './ui/alert';
import { Badge } from './ui/badge';
import { 
  Video,
  Play,
  Clock,
  CreditCard,
  CheckCircle,
  AlertCircle,
  Calendar,
  User,
  Star,
  Loader2,
  FileText,
  Download,
  Eye
} from 'lucide-react';
import { useAuth } from './AuthContext';
import EnhancedVideoViewer from './EnhancedVideoViewer';
import ConsultationPDFViewer from './ConsultationPDFViewer';
import axios from 'axios';

const PersonalConsultations = () => {
  const [consultations, setConsultations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedConsultation, setSelectedConsultation] = useState(null);
  const [selectedPDF, setSelectedPDF] = useState(null);
  const [purchasing, setPurchasing] = useState(null);
  const { user } = useAuth();
  
  const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    fetchConsultations();
  }, []);

  const fetchConsultations = async () => {
    try {
      const response = await axios.get(`${backendUrl}/api/user/consultations`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });
      setConsultations(response.data);
    } catch (error) {
      console.error('Error fetching consultations:', error);
      setError('Ошибка загрузки консультаций');
    } finally {
      setLoading(false);
    }
  };

  const purchaseConsultation = async (consultationId) => {
    setPurchasing(consultationId);
    try {
      const response = await axios.post(`${backendUrl}/api/user/consultations/${consultationId}/purchase`, {}, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.status === 200) {
        fetchConsultations(); // Refresh to show purchased status
        alert('Консультация успешно приобретена!');
      }
    } catch (error) {
      console.error('Error purchasing consultation:', error);
      if (error.response?.status === 402) {
        alert('Недостаточно баллов для покупки консультации');
      } else {
        alert('Ошибка при покупке консультации');
      }
    } finally {
      setPurchasing(null);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500 mr-2" />
        <span>Загружаем консультации...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="numerology-gradient">
        <CardHeader className="text-white">
          <CardTitle className="text-2xl flex items-center">
            <Video className="w-6 h-6 mr-2" />
            Личные Консультации
          </CardTitle>
          <CardDescription className="text-white/90">
            Персональные видеоконсультации от мастера нумерологии
          </CardDescription>
        </CardHeader>
      </Card>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* User Credits Display */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <CreditCard className="w-5 h-5 text-blue-500 mr-2" />
              <span className="text-sm text-gray-600">Ваши баллы:</span>
            </div>
            <Badge variant="outline" className="text-lg px-3 py-1">
              {user?.credits_remaining?.toLocaleString() || 0}
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Consultations List */}
      <div className="grid gap-6">
        {consultations.length === 0 ? (
          <Card>
            <CardContent className="text-center py-12">
              <Video className="w-16 h-16 mx-auto mb-4 text-gray-400" />
              <h3 className="text-lg font-semibold mb-2">Консультаций пока нет</h3>
              <p className="text-gray-600">
                Персональные консультации будут появляться здесь по мере их создания администратором
              </p>
            </CardContent>
          </Card>
        ) : (
          consultations.map((consultation) => (
            <Card key={consultation.id} className="overflow-hidden">
              <CardHeader className="bg-gradient-to-r from-purple-50 to-blue-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-xl mb-2 flex items-center">
                      <Star className="w-5 h-5 text-yellow-500 mr-2" />
                      {consultation.title}
                    </CardTitle>
                    <CardDescription className="text-gray-700 mb-3">
                      {consultation.description}
                    </CardDescription>
                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      <div className="flex items-center">
                        <Calendar className="w-4 h-4 mr-1" />
                        {formatDate(consultation.created_at)}
                      </div>
                      <div className="flex items-center">
                        <User className="w-4 h-4 mr-1" />
                        Персональная консультация
                      </div>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <Badge 
                      variant={consultation.is_purchased ? "default" : "secondary"}
                      className="mb-2"
                    >
                      {consultation.is_purchased ? "Приобретена" : "Доступна для покупки"}
                    </Badge>
                    <div className="text-2xl font-bold text-purple-600">
                      {consultation.cost_credits.toLocaleString()} баллов
                    </div>
                  </div>
                </div>
              </CardHeader>
              
              <CardContent className="p-6">
                {consultation.is_purchased ? (
                  <div className="space-y-4">
                    <Alert>
                      <CheckCircle className="h-4 w-4" />
                      <AlertDescription>
                        Консультация приобретена! Вы можете просмотреть материалы неограниченное количество раз.
                      </AlertDescription>
                    </Alert>
                    
                    {/* Video Material */}
                    {(consultation.video_url || consultation.video_file_id) && (
                      <div className="border rounded-lg p-4 bg-gray-50">
                        <h4 className="font-semibold mb-2 flex items-center">
                          <Video className="w-4 h-4 mr-2 text-blue-600" />
                          Видео консультация
                        </h4>
                        <Button
                          onClick={() => setSelectedConsultation(consultation)}
                          className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
                        >
                          <Play className="w-5 h-5 mr-2" />
                          Смотреть видео
                        </Button>
                      </div>
                    )}
                    
                    {/* PDF Material */}
                    {consultation.pdf_file_id && (
                      <div className="border rounded-lg p-4 bg-gray-50">
                        <h4 className="font-semibold mb-2 flex items-center">
                          <FileText className="w-4 h-4 mr-2 text-red-600" />
                          PDF материалы
                        </h4>
                        <div className="flex gap-2">
                          <Button
                            onClick={() => {
                              setSelectedPDF({
                                url: `${backendUrl}/api/consultations/pdf/${consultation.pdf_file_id}`,
                                title: `${consultation.title} - PDF материалы`,
                                consultation: consultation
                              });
                            }}
                            variant="outline"
                            className="flex-1"
                          >
                            <Eye className="w-4 h-4 mr-2" />
                            Просмотреть
                          </Button>
                          <Button
                            onClick={() => {
                              const link = document.createElement('a');
                              link.href = `${backendUrl}/api/consultations/pdf/${consultation.pdf_file_id}`;
                              link.download = `consultation-${consultation.id}.pdf`;
                              link.click();
                            }}
                            variant="outline"
                            className="flex-1"
                          >
                            <Download className="w-4 h-4 mr-2" />
                            Скачать
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                      <div className="flex items-start">
                        <AlertCircle className="w-5 h-5 text-yellow-600 mr-3 mt-0.5" />
                        <div>
                          <h4 className="font-medium text-yellow-800 mb-1">
                            Персональная консультация
                          </h4>
                          <p className="text-sm text-yellow-700">
                            Эта консультация создана специально для вас. После покупки у вас будет неограниченный доступ к просмотру.
                          </p>
                        </div>
                      </div>
                    </div>
                    
                    {user?.credits_remaining >= consultation.cost_credits ? (
                      <Button
                        onClick={() => purchaseConsultation(consultation.id)}
                        disabled={purchasing === consultation.id}
                        size="lg"
                        className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700"
                      >
                        {purchasing === consultation.id ? (
                          <>
                            <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                            Покупаем...
                          </>
                        ) : (
                          <>
                            <CreditCard className="w-5 h-5 mr-2" />
                            Купить за {consultation.cost_credits.toLocaleString()} баллов
                          </>
                        )}
                      </Button>
                    ) : (
                      <div className="text-center py-4">
                        <Alert variant="destructive">
                          <AlertCircle className="h-4 w-4" />
                          <AlertDescription>
                            Недостаточно баллов. Нужно: {consultation.cost_credits.toLocaleString()}, 
                            у вас: {user?.credits_remaining?.toLocaleString() || 0}
                          </AlertDescription>
                        </Alert>
                        <Button
                          variant="outline"
                          className="mt-3"
                          onClick={() => {
                            // Navigate to payment or credits page
                            window.open('/payment', '_blank');
                          }}
                        >
                          <CreditCard className="w-4 h-4 mr-2" />
                          Пополнить баллы
                        </Button>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Enhanced Video Player Modal */}
      {selectedConsultation && (
        <EnhancedVideoViewer
          videoUrl={
            selectedConsultation.video_url || 
            (selectedConsultation.video_file_id ? `${backendUrl}/api/consultations/video/${selectedConsultation.video_file_id}` : null)
          }
          title={selectedConsultation.title}
          description={selectedConsultation.description}
          cost_credits={selectedConsultation.cost_credits}
          consultation={selectedConsultation}
          backendUrl={backendUrl}
          onClose={() => setSelectedConsultation(null)}
        />
      )}

      {/* PDF Viewer Modal */}
      {selectedPDF && (
        <ConsultationPDFViewer
          pdfUrl={selectedPDF.url}
          title={selectedPDF.title}
          onClose={() => setSelectedPDF(null)}
        />
      )}
    </div>
  );
};

export default PersonalConsultations;