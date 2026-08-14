{{- define "inveniordm-api-proxy.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s" .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end }}

{{- define "inveniordm-api-proxy.labels" -}}
app.kubernetes.io/name: inveniordm-api-proxy
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
{{- end }}

{{- define "inveniordm-api-proxy.selectorLabels" -}}
app.kubernetes.io/name: inveniordm-api-proxy
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Public URL of this proxy. The OAuth application registered on the InvenioRDM
instance must have exactly "<publicUrl>/auth/callback" as its redirect URI.
*/}}
{{- define "inveniordm-api-proxy.publicUrl" -}}
{{- if .Values.proxy.publicUrl -}}
{{- .Values.proxy.publicUrl | trimSuffix "/" -}}
{{- else -}}
{{- printf "https://%s" (required "either proxy.publicUrl or ingress.host must be set" .Values.ingress.host) -}}
{{- end -}}
{{- end }}

{{/*
Name of the secret holding INVENIORDM_CLIENT_SECRET. Points at an
externally-managed secret (a SealedSecret, in the VRE) unless one is created
inline via oauth.clientSecret, which is intended for dev only.
*/}}
{{- define "inveniordm-api-proxy.secretName" -}}
{{- if .Values.oauth.existingSecret -}}
{{- .Values.oauth.existingSecret -}}
{{- else -}}
{{- printf "%s-oauth" (include "inveniordm-api-proxy.fullname" .) -}}
{{- end -}}
{{- end }}
