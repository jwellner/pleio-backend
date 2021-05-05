{{- define "backend2.name" -}}
{{- .Release.Name | trunc 63  -}}
{{- end -}}

{{- define "backend2.secretsName" -}}
{{- printf "%s-secrets" ((include "backend2.name" .)) -}}
{{- end -}}

{{- define "backend2.tlsSecretName" -}}
{{- printf "tls-%s" ((include "backend2.name" .)) -}}
{{- end -}}

{{- define "backend2.frontendName" -}}
{{- printf "%s-frontend" ((include "backend2.name" . )) -}}
{{- end -}}

{{- define "backend2.tempStorageName" -}}
{{- printf "%s-tmp" ((include "backend2.name" . )) -}}
{{- end -}}

{{- define "backend2.dataStorageName" -}}
{{- printf "%s-data" ((include "backend2.name" . )) -}}
{{- end -}}

{{- define "backend2.apiName" -}}
{{- printf "%s-api" ((include "backend2.name" . )) -}}
{{- end -}}

{{- define "backend2.adminName" -}}
{{- printf "%s-admin" ((include "backend2.name" . )) -}}
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
