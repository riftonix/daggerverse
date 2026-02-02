{{/*
   * Generate kubernetes.io/dockerconfigjson string.
*/}}
{{- define "ns-configurator.dockerconfigjson" }}
{{- $auths := dict }}
{{- range .registries }}
{{- $auth := dict "auth" (printf "%s:%s" .username .password | b64enc) }}
{{- $_ := set $auths .host $auth }}
{{- end }}
{{- $config := dict "auths" $auths }}
{{- toJson $config | b64enc -}}
{{- end }}
