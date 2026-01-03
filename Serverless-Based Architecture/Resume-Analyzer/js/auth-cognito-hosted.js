// js/auth-cognito-hosted.js
// Cognito Hosted UI Authentication

const CONFIG = {
    region: 'us-east-1',
    userPoolId: 'us-east-1_121918DAD',
    clientId: '1e14cc5a6p1ih9213oonht6mr0',
    clientSecret: 'KFVGDBVKLVBASFHavhdsvljdvlnvdsvdsvds',
    domain: 'resume-analyzer-bsu.auth.us-east-1.amazoncognito.com',
    redirectSignIn: 'https://daajadadfjaf.cloudfront.net/html/callback.html',
    redirectSignOut: 'https://daajadadfjaf.cloudfront.net/index.html',
    scope: ['openid', 'email', 'phone', 'profile']
};

class CognitoAuth {
    constructor(config) {
        this.config = config;
        this.cognitoAuthUrl = `https://${config.domain}`;
        console.log('CognitoAuth initialized with URL:', this.cognitoAuthUrl);
    }

    login() {
        const loginUrl = `${this.cognitoAuthUrl}/login?` +
            `client_id=${this.config.clientId}&` +
            `response_type=code&` +
            `scope=${this.config.scope.join('+')}&` +
            `redirect_uri=${encodeURIComponent(this.config.redirectSignIn)}`;
        
        console.log(' Redirecting to Cognito login...');
        console.log('Login URL:', loginUrl);
        
        window.location.href = loginUrl;
    }

    signup() {
        const signupUrl = `${this.cognitoAuthUrl}/signup?` +
            `client_id=${this.config.clientId}&` +
            `response_type=code&` +
            `scope=${this.config.scope.join('+')}&` +
            `redirect_uri=${encodeURIComponent(this.config.redirectSignIn)}`;
        
        console.log(' Redirecting to Cognito signup...');
        console.log('Signup URL:', signupUrl);
        
        window.location.href = signupUrl;
    }

    logout() {
        console.log(' Logging out...');
        
        localStorage.removeItem('idToken');
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('userSession');
        
        const logoutUrl = `${this.cognitoAuthUrl}/logout?` +
            `client_id=${this.config.clientId}&` +
            `logout_uri=${encodeURIComponent(this.config.redirectSignOut)}`;
        
        console.log('Logout URL:', logoutUrl);
        window.location.href = logoutUrl;
    }

    async handleCallback() {
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        
        if (!code) {
            console.error('No authorization code found');
            return null;
        }

        console.log(' Authorization code received, exchanging for tokens...');

        try {
            const tokens = await this.exchangeCodeForTokens(code);
            
            localStorage.setItem('idToken', tokens.id_token);
            localStorage.setItem('accessToken', tokens.access_token);
            localStorage.setItem('refreshToken', tokens.refresh_token);
            
            const userInfo = this.parseJwt(tokens.id_token);
            localStorage.setItem('userSession', JSON.stringify({
                email: userInfo.email,
                name: userInfo.name || userInfo.email,
                sub: userInfo.sub
            }));
            
            console.log(' User authenticated successfully');
            return userInfo;
        } catch (error) {
            console.error(' Error handling callback:', error);
            return null;
        }
    }

    async exchangeCodeForTokens(code) {
        const tokenUrl = `${this.cognitoAuthUrl}/oauth2/token`;
        
        console.log('=== TOKEN EXCHANGE ===');
        console.log('Token URL:', tokenUrl);
        console.log('Authorization code:', code.substring(0, 20) + '...');
        
        const body = new URLSearchParams({
            grant_type: 'authorization_code',
            client_id: this.config.clientId,
            code: code,
            redirect_uri: this.config.redirectSignIn
        });

        const auth = btoa(`${this.config.clientId}:${this.config.clientSecret}`);

        try {
            const response = await fetch(tokenUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Authorization': `Basic ${auth}`
                },
                body: body.toString()
            });

            console.log('Response status:', response.status);
            
            const responseText = await response.text();

            if (!response.ok) {
                let errorData;
                try {
                    errorData = JSON.parse(responseText);
                } catch (e) {
                    errorData = { error: 'unknown', message: responseText };
                }
                console.error('Token exchange failed:', errorData);
                throw new Error(`Failed to exchange code for tokens: ${errorData.error || response.status}`);
            }

            const tokens = JSON.parse(responseText);
            console.log(' Tokens received successfully');
            return tokens;
        } catch (error) {
            console.error('Token exchange error:', error);
            throw error;
        }
    }

    parseJwt(token) {
        try {
            const base64Url = token.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(
                atob(base64).split('').map(function(c) {
                    return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
                }).join('')
            );
            return JSON.parse(jsonPayload);
        } catch (error) {
            console.error('Error parsing JWT:', error);
            return null;
        }
    }

    isAuthenticated() {
        const idToken = localStorage.getItem('idToken');
        if (!idToken) return false;

        try {
            const decoded = this.parseJwt(idToken);
            if (!decoded) return false;
            
            const currentTime = Date.now() / 1000;
            return decoded.exp > currentTime;
        } catch (error) {
            console.error('Error checking authentication:', error);
            return false;
        }
    }

    getCurrentUser() {
        const userSession = localStorage.getItem('userSession');
        return userSession ? JSON.parse(userSession) : null;
    }
}

const cognitoAuth = new CognitoAuth(CONFIG);
window.CognitoAuth = cognitoAuth;

console.log(' CognitoAuth loaded and ready');