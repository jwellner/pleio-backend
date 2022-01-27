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
{{- if .Values.storage.existingTempStorage -}}
{{- .Values.storage.existingTempStorage -}}
{{- else -}}
{{- printf "%s-tmp" ((include "backend2.name" . )) -}}
{{- end -}}
{{- end -}}

{{- define "backend2.dataStorageName" -}}
{{- if .Values.storage.existingDataStorage -}}
{{- .Values.storage.existingDataStorage -}}
{{- else -}}
{{- printf "%s-data" ((include "backend2.name" . )) -}}
{{- end -}}
{{- end -}}

{{- define "backend2.backupStorageName" -}}
{{- if .Values.storage.existingBackupStorage -}}
{{- .Values.storage.existingBackupStorage -}}
{{- else -}}
{{- printf "%s-backup" ((include "backend2.name" . )) -}}
{{- end -}}
{{- end -}}

{{- define "backend2.apiName" -}}
{{- printf "%s-api" ((include "backend2.name" . )) -}}
{{- end -}}

{{- define "backend2.adminName" -}}
{{- printf "%s-admin" ((include "backend2.name" . )) -}}
{{- end -}}

{{- define "backend2.backgroundSchedulerName" -}}
{{- printf "%s-background-scheduler" ((include "backend2.name" . )) -}}
{{- end -}}

{{- define "backend2.backgroundWorkerName" -}}
{{- printf "%s-background-worker" ((include "backend2.name" . )) -}}
{{- end -}}

{{- define "backend2.filecleanup" -}}
{{- printf "%s-filecleanup" ((include "backend2.name" . )) -}}
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

{{- define "backend2.hosts" -}}
- {{ . | quote }}
{{- if not (hasPrefix "*" .) }}
- {{ printf "www.%s" . | quote }}
{{- end }}
{{- end -}}
