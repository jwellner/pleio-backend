{{- define "backend2.name" -}}
{{- .Release.Name | trunc 63  -}}
{{- end -}}

{{- define "backend2.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "backend2.labels" -}}
helm.sh/chart: {{ include "backend2.chart" . }}
{{ include "backend2.selectorLabels" . }}
{{- end -}}

{{- define "backend2.selectorLabels" -}}
app.kubernetes.io/name: {{ include "backend2.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- if .Component }}
app.kubernetes.io/component: {{ .Component }}
{{- end }}
{{- end -}}
