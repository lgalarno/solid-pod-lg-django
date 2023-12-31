from django import forms

import httpx

from connector.oidc import provider_discovery
from .models import SolidPod, OpenIDprovider


class OpenIDproviderForm(forms.ModelForm):

    class Meta:
        model = OpenIDprovider
        fields = (
            'url',
            'provider_info'
        )

    def clean(self):
        cleaned_data = self.cleaned_data
        provider_url = cleaned_data.get("url")
        if provider_url:
            provider_url = provider_url.strip()
            if provider_url[-1] != '/':
                provider_url = provider_url + '/'
            try:
                r = httpx.get(provider_url)
                provider_info, valid = provider_discovery(provider_url)
                if valid:
                    cleaned_data['provider_info'] = provider_info
                    cleaned_data['url'] = provider_url
                else:
                    # can't get provider_info
                    self.add_error('provider_info', f"Invalid issuer. {provider_info}")
            except:
                self.add_error('url', f"Invalid URL. Please, try again or check the address.")
        return cleaned_data


class SolidPodForm(forms.ModelForm):

    class Meta:
        model = SolidPod
        fields = (
            'name',
            'url',
        )

    def clean_url(self):
        pod_url = self.cleaned_data.get("url")
        if pod_url[-1] != '/':
            pod_url = pod_url + '/'
        try:
            r = httpx.get(pod_url)
        except:
            raise forms.ValidationError(f"Invalid URL. Please, try again or check the address.")
        if r.status_code == 200:
            if 'text/turtle' not in r.headers.get('Content-Type'):
                raise forms.ValidationError(f"Not a valid pod URL.")
        elif r.status_code == 404:
            raise forms.ValidationError(f"The pod does not exist {r}")
        else:
            raise forms.ValidationError(f"Error {r}")
        return pod_url
