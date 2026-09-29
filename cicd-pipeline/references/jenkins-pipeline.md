# Jenkins Pipeline (moved from SKILL.md body — pointer only there)

## Jenkins Pipeline

```groovy
pipeline {
    agent any

    environment {
        NODE_VERSION = '20'
        CI = 'true'
    }

    options {
        timeout(time: 60, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install') {
            steps {
                sh 'npm ci'
            }
        }

        stage('Static Analysis') {
            parallel {
                stage('Lint') {
                    steps {
                        sh 'npx eslint . --max-warnings=0'
                    }
                }
                stage('Type Check') {
                    steps {
                        sh 'npx tsc --noEmit'
                    }
                }
            }
        }

        stage('Unit Tests') {
            steps {
                sh 'npx jest --coverage --ci --reporters=default --reporters=jest-junit'
            }
            post {
                always {
                    junit 'test-results/unit/*.xml'
                    publishHTML(target: [
                        reportDir: 'coverage/lcov-report',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                }
            }
        }

        stage('E2E Tests') {
            steps {
                sh 'npx playwright install --with-deps chromium'
                sh 'npm run start:test &'
                sh 'npx wait-on http://<app-host>:<port> --timeout 30000'
                sh 'npx playwright test'
            }
            post {
                always {
                    publishHTML(target: [
                        reportDir: 'playwright-report',
                        reportFiles: 'index.html',
                        reportName: 'E2E Test Report'
                    ])
                    archiveArtifacts artifacts: 'test-results/**/*', allowEmptyArchive: true
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        failure {
            slackSend(
                channel: '#test-alerts',
                color: 'danger',
                message: "Build Failed: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
            )
        }
        success {
            slackSend(
                channel: '#test-results',
                color: 'good',
                message: "Build Passed: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
            )
        }
    }
}
```
