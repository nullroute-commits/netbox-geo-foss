// Enterprise CI/CD Jenkins Pipeline
pipeline {
    agent {
        label 'docker-agent'
    }
    
    options {
        timestamps()
        timeout(time: 1, unit: 'HOURS')
        buildDiscarder(logRotator(numToKeepStr: '10'))
        disableConcurrentBuilds()
    }
    
    environment {
        DOCKER_BUILDKIT = '1'
        COMPOSE_DOCKER_CLI_BUILD = '1'
        BUILD_ID = "${env.BUILD_NUMBER}"
        COMMIT_SHA = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()
        DOCKER_REGISTRY = credentials('docker-registry')
        SONAR_TOKEN = credentials('sonar-token')
        ANSIBLE_VAULT_PASSWORD = credentials('ansible-vault-password')
    }
    
    stages {
        stage('Setup') {
            steps {
                echo "Setting up CI/CD environment..."
                sh '''
                    docker compose -f docker-compose.ci.yml pull
                    docker compose -f docker-compose.pipeline.yml build
                '''
            }
        }
        
        stage('Code Quality') {
            parallel {
                stage('Lint') {
                    steps {
                        script {
                            docker.image('python:3.13-slim').inside {
                                sh '''
                                    pip install -e ".[dev]"
                                    black --check src tests
                                    ruff check src tests
                                    mypy src
                                '''
                            }
                        }
                    }
                }
                
                stage('Security Scan') {
                    steps {
                        script {
                            sh '''
                                docker compose -f docker-compose.pipeline.yml \
                                    run --rm \
                                    -e PIPELINE_COMMAND=security \
                                    pipeline-executor security
                            '''
                        }
                    }
                    post {
                        always {
                            archiveArtifacts artifacts: '*-report.json', allowEmptyArchive: true
                        }
                    }
                }
            }
        }
        
        stage('Test') {
            parallel {
                stage('Unit Tests') {
                    steps {
                        sh '''
                            docker compose -f docker-compose.pipeline.yml \
                                run --rm \
                                -e ENVIRONMENT=test \
                                -e PIPELINE_COMMAND=test \
                                pipeline-executor test
                        '''
                    }
                    post {
                        always {
                            junit 'junit.xml'
                            publishHTML([
                                allowMissing: false,
                                alwaysLinkToLastBuild: true,
                                keepAll: true,
                                reportDir: 'htmlcov',
                                reportFiles: 'index.html',
                                reportName: 'Coverage Report'
                            ])
                        }
                    }
                }
                
                stage('Integration Tests') {
                    steps {
                        sh '''
                            docker compose -f docker-compose.base.yml \
                                           -f docker-compose.test.yml \
                                           up -d
                            
                            docker compose -f docker-compose.base.yml \
                                           -f docker-compose.test.yml \
                                           exec -T app pytest tests/integration -v
                        '''
                    }
                    post {
                        always {
                            sh '''
                                docker compose -f docker-compose.base.yml \
                                               -f docker-compose.test.yml \
                                               down -v
                            '''
                        }
                    }
                }
            }
        }
        
        stage('Build') {
            when {
                anyOf {
                    branch 'main'
                    branch 'develop'
                    tag pattern: "v\\d+\\.\\d+\\.\\d+", comparator: "REGEXP"
                }
            }
            steps {
                script {
                    def imageName = "${DOCKER_REGISTRY}/enterprise-app"
                    def imageTag = "${COMMIT_SHA}"
                    
                    sh """
                        docker build -t ${imageName}:${imageTag} .
                        docker tag ${imageName}:${imageTag} ${imageName}:${env.BRANCH_NAME}
                    """
                    
                    if (env.TAG_NAME) {
                        sh "docker tag ${imageName}:${imageTag} ${imageName}:${env.TAG_NAME}"
                        sh "docker tag ${imageName}:${imageTag} ${imageName}:latest"
                    }
                }
            }
        }
        
        stage('Container Security Scan') {
            when {
                anyOf {
                    branch 'main'
                    branch 'develop'
                }
            }
            steps {
                sh '''
                    docker run --rm \
                        -v /var/run/docker.sock:/var/run/docker.sock \
                        aquasec/trivy:latest image \
                        --severity HIGH,CRITICAL \
                        --format json \
                        --output trivy-results.json \
                        ${DOCKER_REGISTRY}/enterprise-app:${COMMIT_SHA}
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'trivy-results.json', allowEmptyArchive: true
                }
            }
        }
        
        stage('Push to Registry') {
            when {
                anyOf {
                    branch 'main'
                    tag pattern: "v\\d+\\.\\d+\\.\\d+", comparator: "REGEXP"
                }
            }
            steps {
                script {
                    docker.withRegistry("https://${DOCKER_REGISTRY}", 'docker-registry-creds') {
                        def imageName = "${DOCKER_REGISTRY}/enterprise-app"
                        
                        sh "docker push ${imageName}:${COMMIT_SHA}"
                        sh "docker push ${imageName}:${env.BRANCH_NAME}"
                        
                        if (env.TAG_NAME) {
                            sh "docker push ${imageName}:${env.TAG_NAME}"
                            sh "docker push ${imageName}:latest"
                        }
                    }
                }
            }
        }
        
        stage('Deploy') {
            when {
                branch 'main'
            }
            stages {
                stage('Deploy to Staging') {
                    steps {
                        sh '''
                            docker compose -f docker-compose.pipeline.yml \
                                run --rm \
                                -e ENVIRONMENT=staging \
                                -e COMMIT_SHA=${COMMIT_SHA} \
                                -e ANSIBLE_VAULT_PASSWORD_FILE=/tmp/vault-pass \
                                -v ${ANSIBLE_VAULT_PASSWORD}:/tmp/vault-pass:ro \
                                pipeline-executor deploy
                        '''
                    }
                }
                
                stage('Smoke Tests') {
                    steps {
                        sh '''
                            docker run --rm \
                                --network host \
                                curlimages/curl:latest \
                                curl -f https://staging.example.com/health || exit 1
                        '''
                    }
                }
                
                stage('Performance Tests') {
                    steps {
                        sh '''
                            docker run --rm \
                                -v ${WORKSPACE}/tests/performance:/scripts \
                                -v ${WORKSPACE}/reports:/reports \
                                grafana/k6:latest run \
                                --out json=/reports/k6-results.json \
                                /scripts/load-test.js
                        '''
                    }
                    post {
                        always {
                            archiveArtifacts artifacts: 'reports/k6-results.json', allowEmptyArchive: true
                        }
                    }
                }
                
                stage('Deploy to Production') {
                    when {
                        tag pattern: "v\\d+\\.\\d+\\.\\d+", comparator: "REGEXP"
                    }
                    input {
                        message "Deploy to production?"
                        ok "Deploy"
                        parameters {
                            booleanParam(name: 'CONFIRM_DEPLOY', defaultValue: false, description: 'Confirm production deployment')
                        }
                    }
                    steps {
                        script {
                            if (params.CONFIRM_DEPLOY) {
                                sh '''
                                    docker compose -f docker-compose.pipeline.yml \
                                        run --rm \
                                        -e ENVIRONMENT=prod \
                                        -e COMMIT_SHA=${COMMIT_SHA} \
                                        -e ANSIBLE_VAULT_PASSWORD_FILE=/tmp/vault-pass \
                                        -v ${ANSIBLE_VAULT_PASSWORD}:/tmp/vault-pass:ro \
                                        pipeline-executor deploy
                                '''
                            } else {
                                error "Production deployment not confirmed"
                            }
                        }
                    }
                }
            }
        }
    }
    
    post {
        always {
            // Clean up
            sh '''
                docker compose -f docker-compose.pipeline.yml down -v || true
                docker system prune -f || true
            '''
            
            // Send notifications
            script {
                def status = currentBuild.result ?: 'SUCCESS'
                def color = status == 'SUCCESS' ? 'good' : 'danger'
                
                slackSend(
                    channel: '#ci-cd',
                    color: color,
                    message: "Build ${env.BUILD_NUMBER} - ${status}\nBranch: ${env.BRANCH_NAME}\nCommit: ${COMMIT_SHA}"
                )
            }
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}