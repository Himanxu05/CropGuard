import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { diseaseAPI } from '../services/api'
import { Upload, Camera, AlertTriangle, CheckCircle, Loader2, Eye, EyeOff, Bug } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

export default function DiseaseDetection() {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [result, setResult] = useState(null)
  const [gradcam, setGradcam] = useState(null)
  const [showGradcam, setShowGradcam] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const onDrop = useCallback((accepted) => {
    if (accepted.length > 0) {
      const f = accepted[0]
      setFile(f)
      setPreview(URL.createObjectURL(f))
      setResult(null); setGradcam(null); setError('')
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: { 'image/jpeg': [], 'image/png': [] }, maxSize: 10 * 1024 * 1024, multiple: false,
  })

  const handlePredict = async () => {
    if (!file) return
    setLoading(true); setError('')
    const formData = new FormData()
    formData.append('image', file)

    try {
      const { data } = await diseaseAPI.predict(formData)
      setResult(data)
      if (data.gradcam_available && data.id) {
        try {
          const gcRes = await diseaseAPI.gradcam(data.id)
          setGradcam(URL.createObjectURL(gcRes.data))
        } catch { /* gradcam optional */ }
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Prediction failed')
    } finally { setLoading(false) }
  }

  const severityColor = { High: 'text-red-400', Medium: 'text-accent-400', Low: 'text-primary-400', Uncertain: 'text-gray-400' }

  const chartData = result?.top3_predictions?.map(p => ({
    name: (p.class || p).replace(/___/g, ' - ').replace(/_/g, ' ').substring(0, 25),
    confidence: ((p.confidence || p) * 100).toFixed(1),
  })) || []

  return (
    <div className="fade-in space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
          <Bug className="w-8 h-8 text-primary-400" /> Disease Detection
        </h1>
        <p className="text-gray-400 mt-1">Upload a leaf image for AI-powered disease diagnosis</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upload Area */}
        <div className="glass rounded-2xl p-6 space-y-4">
          <h2 className="text-lg font-semibold text-white">Upload Leaf Image</h2>
          <div {...getRootProps()} className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all
            ${isDragActive ? 'border-primary-400 bg-primary-500/10' : 'border-white/10 hover:border-primary-500/40'}`}>
            <input {...getInputProps()} />
            {preview ? (
              <img src={preview} alt="Preview" className="max-h-64 mx-auto rounded-lg object-contain" />
            ) : (
              <>
                <Camera className="w-16 h-16 mx-auto text-gray-600 mb-4" />
                <p className="text-gray-400">{isDragActive ? 'Drop image here...' : 'Drag & drop or click to upload'}</p>
                <p className="text-xs text-gray-600 mt-2">JPEG, PNG • Max 10MB</p>
              </>
            )}
          </div>

          {file && (
            <button onClick={handlePredict} disabled={loading}
              className="w-full py-3 rounded-xl gradient-primary text-white font-semibold shadow-lg shadow-primary-500/25 disabled:opacity-50 flex items-center justify-center gap-2">
              {loading ? <><Loader2 className="w-5 h-5 animate-spin" /> Analyzing...</> : <><Upload className="w-5 h-5" /> Analyze Image</>}
            </button>
          )}

          {error && (
            <div className="flex items-center gap-2 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
              <AlertTriangle className="w-5 h-5 flex-shrink-0" />{error}
            </div>
          )}
        </div>

        {/* Results */}
        <div className="glass rounded-2xl p-6 space-y-4">
          <h2 className="text-lg font-semibold text-white">Diagnosis Result</h2>

          {result ? (
            <div className="space-y-4 fade-in">
              {/* Grad-CAM toggle */}
              {gradcam && (
                <div className="relative">
                  <img src={showGradcam ? gradcam : preview} alt="Analysis" className="w-full rounded-xl object-contain max-h-48" />
                  <button onClick={() => setShowGradcam(!showGradcam)}
                    className="absolute top-2 right-2 px-3 py-1.5 rounded-lg glass text-xs text-white flex items-center gap-1">
                    {showGradcam ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                    {showGradcam ? 'Original' : 'Grad-CAM'}
                  </button>
                </div>
              )}

              <div className="p-4 rounded-xl bg-primary-500/10 border border-primary-500/20">
                <div className="flex items-center gap-2 mb-1">
                  <CheckCircle className="w-5 h-5 text-primary-400" />
                  <span className="text-lg font-semibold text-white">
                    {result.predicted_class?.replace(/___/g, ' — ').replace(/_/g, ' ')}
                  </span>
                </div>
                <p className="text-primary-400 text-2xl font-bold">{(result.confidence * 100).toFixed(1)}%</p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-xl bg-white/3">
                  <p className="text-xs text-gray-500">Severity</p>
                  <p className={`text-lg font-semibold ${severityColor[result.severity]}`}>{result.severity}</p>
                </div>
                <div className="p-3 rounded-xl bg-white/3">
                  <p className="text-xs text-gray-500">SHA-256 Verified</p>
                  <p className="text-lg font-semibold text-primary-400">✓ Verified</p>
                </div>
              </div>

              {result.treatment && (
                <div className="p-4 rounded-xl bg-accent-500/10 border border-accent-500/20">
                  <p className="text-sm font-medium text-accent-400 mb-1">💊 Treatment</p>
                  <p className="text-sm text-gray-300">{result.treatment}</p>
                </div>
              )}

              {chartData.length > 0 && (
                <div>
                  <p className="text-sm text-gray-400 mb-2">Top Predictions</p>
                  <ResponsiveContainer width="100%" height={120}>
                    <BarChart data={chartData} layout="vertical">
                      <XAxis type="number" domain={[0, 100]} tick={{ fill: '#9ca3af', fontSize: 11 }} />
                      <YAxis type="category" dataKey="name" width={150} tick={{ fill: '#d1d5db', fontSize: 10 }} />
                      <Tooltip contentStyle={{ background: '#1a1f2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff' }} />
                      <Bar dataKey="confidence" radius={[0, 6, 6, 0]}>
                        {chartData.map((_, i) => <Cell key={i} fill={i === 0 ? '#22c55e' : i === 1 ? '#3b82f6' : '#6b7280'} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-16 text-gray-500">
              <Bug className="w-16 h-16 mb-4 opacity-20" />
              <p>Upload an image to see results</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
