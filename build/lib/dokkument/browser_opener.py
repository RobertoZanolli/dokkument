"""
BrowserOpener - Gestisce l'apertura degli URL nel browser
Supporta Windows, Linux e macOS con gestione errori appropriata
"""

import webbrowser
import subprocess
import sys
import shutil
from pathlib import Path
from typing import Optional, List
from urllib.parse import urlparse
import platform


class BrowserOpener:
    """Gestisce l'apertura degli URL nel browser predefinito del sistema"""
    
    def __init__(self):
        self.platform = platform.system().lower()
        self._preferred_browsers = self._get_system_browsers()
    
    def _get_system_browsers(self) -> List[str]:
        """Restituisce una lista di browser disponibili per il sistema corrente"""
        browsers = []
        
        if self.platform == 'windows':
            # Windows - controlla i browser comuni
            browsers = ['firefox', 'chrome', 'msedge', 'iexplore']
        elif self.platform == 'darwin':  # macOS
            # macOS - controlla browser comuni
            browsers = ['safari', 'firefox', 'chrome', 'opera']
        else:  # Linux e altri Unix
            # Linux - controlla browser comuni
            browsers = ['firefox', 'google-chrome', 'chromium-browser', 'opera']
        
        # Filtra solo i browser effettivamente disponibili
        available_browsers = []
        for browser in browsers:
            if shutil.which(browser) or self._browser_exists(browser):
                available_browsers.append(browser)
        
        return available_browsers
    
    def _browser_exists(self, browser_name: str) -> bool:
        """Controlla se un browser specifico esiste nel sistema"""
        try:
            if self.platform == 'darwin':
                # Su macOS controlla nelle Applications
                app_paths = [
                    f"/Applications/{browser_name.title()}.app",
                    f"/Applications/Google Chrome.app" if browser_name == 'chrome' else None,
                    f"/Applications/Microsoft Edge.app" if browser_name == 'msedge' else None,
                ]
                return any(Path(path).exists() for path in app_paths if path)
            
            elif self.platform == 'windows':
                # Su Windows controlla i registri comuni o path noti
                common_paths = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe" if browser_name == 'chrome' else None,
                    r"C:\Program Files\Mozilla Firefox\firefox.exe" if browser_name == 'firefox' else None,
                    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" if browser_name == 'msedge' else None,
                ]
                return any(Path(path).exists() for path in common_paths if path)
            
            else:
                # Su Linux usa which
                return shutil.which(browser_name) is not None
                
        except Exception:
            return False
        
        return False
    
    def open_url(self, url: str, browser_name: Optional[str] = None) -> bool:
        """
        Apre un URL nel browser specificato o in quello predefinito
        
        Args:
            url: URL da aprire
            browser_name: Nome specifico del browser (opzionale)
            
        Returns:
            bool: True se l'apertura ha avuto successo, False altrimenti
        """
        if not self._is_valid_url(url):
            print(f"Errore: URL non valido: {url}")
            return False
        
        try:
            if browser_name:
                return self._open_with_specific_browser(url, browser_name)
            else:
                return self._open_with_default_browser(url)
                
        except Exception as e:
            print(f"Errore nell'apertura dell'URL {url}: {e}")
            return False
    
    def _is_valid_url(self, url: str) -> bool:
        """Valida se l'URL è ben formato"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
        except Exception:
            return False
    
    def _open_with_default_browser(self, url: str) -> bool:
        """Apre l'URL con il browser predefinito del sistema"""
        try:
            # Primo tentativo: usa webbrowser (funziona nella maggior parte dei casi)
            webbrowser.open(url)
            return True
            
        except Exception as e1:
            print(f"Errore con webbrowser.open: {e1}")
            
            # Secondo tentativo: usa comandi specifici del sistema
            try:
                if self.platform == 'windows':
                    subprocess.run(['start', url], shell=True, check=True)
                elif self.platform == 'darwin':
                    subprocess.run(['open', url], check=True)
                else:  # Linux e altri Unix
                    subprocess.run(['xdg-open', url], check=True)
                    
                return True
                
            except Exception as e2:
                print(f"Errore con comando di sistema: {e2}")
                return False
    
    def _open_with_specific_browser(self, url: str, browser_name: str) -> bool:
        """Apre l'URL con un browser specifico"""
        try:
            # Primo tentativo: usa webbrowser con il browser specificato
            try:
                browser = webbrowser.get(browser_name)
                browser.open(url)
                return True
            except webbrowser.Error:
                pass
            
            # Secondo tentativo: usa comandi diretti
            if self.platform == 'windows':
                if browser_name.lower() in ['chrome', 'google-chrome']:
                    subprocess.run([
                        r"C:\Program Files\Google\Chrome\Application\chrome.exe", 
                        url
                    ], check=True)
                elif browser_name.lower() == 'firefox':
                    subprocess.run([
                        r"C:\Program Files\Mozilla Firefox\firefox.exe", 
                        url
                    ], check=True)
                elif browser_name.lower() in ['msedge', 'edge']:
                    subprocess.run([
                        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", 
                        url
                    ], check=True)
                else:
                    return False
                    
            elif self.platform == 'darwin':
                if browser_name.lower() == 'safari':
                    subprocess.run(['open', '-a', 'Safari', url], check=True)
                elif browser_name.lower() in ['chrome', 'google-chrome']:
                    subprocess.run(['open', '-a', 'Google Chrome', url], check=True)
                elif browser_name.lower() == 'firefox':
                    subprocess.run(['open', '-a', 'Firefox', url], check=True)
                elif browser_name.lower() == 'opera':
                    subprocess.run(['open', '-a', 'Opera', url], check=True)
                else:
                    return False
                    
            else:  # Linux
                # Su Linux, prova ad usare il nome del browser direttamente
                subprocess.run([browser_name, url], check=True)
            
            return True
            
        except Exception as e:
            print(f"Errore nell'apertura con browser specifico {browser_name}: {e}")
            return False
    
    def open_multiple_urls(self, urls: List[str], browser_name: Optional[str] = None, delay_seconds: float = 0.5) -> List[bool]:
        """
        Apre múltipli URL
        
        Args:
            urls: Lista di URL da aprire
            browser_name: Nome specifico del browser (opzionale)
            delay_seconds: Ritardo tra le aperture per evitare problemi
            
        Returns:
            List[bool]: Lista di risultati per ogni URL
        """
        import time
        
        results = []
        for i, url in enumerate(urls):
            if i > 0 and delay_seconds > 0:
                time.sleep(delay_seconds)
            
            result = self.open_url(url, browser_name)
            results.append(result)
            
            if result:
                print(f" Aperto: {url}")
            else:
                print(f" Fallito: {url}")
        
        return results
    
    def get_available_browsers(self) -> List[str]:
        """Restituisce la lista di browser disponibili nel sistema"""
        return self._preferred_browsers.copy()
    
    def test_browser_availability(self) -> dict:
        """
        Testa la disponibilità di browser comuni nel sistema
        
        Returns:
            dict: Dizionario con browser come chiave e disponibilità come valore
        """
        common_browsers = {
            'default': 'Browser predefinito del sistema',
            'firefox': 'Mozilla Firefox',
            'chrome': 'Google Chrome',
            'safari': 'Safari (solo macOS)',
            'msedge': 'Microsoft Edge',
            'opera': 'Opera'
        }
        
        results = {}
        
        for browser_key, browser_name in common_browsers.items():
            if browser_key == 'default':
                # Testa il browser predefinito
                test_result = self._test_default_browser()
                results[browser_name] = test_result
            else:
                # Testa browser specifici
                if browser_key == 'safari' and self.platform != 'darwin':
                    results[browser_name] = False  # Safari solo su macOS
                else:
                    results[browser_name] = browser_key in self._preferred_browsers
        
        return results
    
    def _test_default_browser(self) -> bool:
        """Testa se il browser predefinito è disponibile"""
        try:
            # Test semplice senza aprire effettivamente nulla
            webbrowser.get()
            return True
        except Exception:
            return False
    
    def print_browser_info(self):
        """Stampa informazioni sui browser disponibili"""
        print(f"Sistema operativo: {platform.system()} {platform.release()}")
        print(f"Browser disponibili:")
        
        availability = self.test_browser_availability()
        for browser, available in availability.items():
            status = " Disponibile" if available else " Non disponibile"
            print(f"  {browser}: {status}")
        
        if self._preferred_browsers:
            print(f"\nBrowser preferiti rilevati: {', '.join(self._preferred_browsers)}")
        else:
            print("\nNessun browser specifico rilevato, verrà usato il predefinito del sistema")