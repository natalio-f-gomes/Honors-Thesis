# Honors-Thesis

## Server-Based vs. Serverless Architecture: A Comparative Study

**Honors Thesis by Natalio F. Gomes**  
*Bridgewater State University*

## Abstract

This thesis investigates the fundamental question: **"How do server-based architectures compare to serverless architectures in terms of development, deployment process, scalability, and cost-effectiveness?"**

Through the development of a resume analyzer web application built using both architectural approaches, this research provides empirical evidence and hands-on insights into the practical differences between traditional server-based infrastructure and modern serverless computing.

## Research Overview

### Application: Resume Analyzer

A web application that:
- Analyzes user resumes using AI (Claude AI)
- Fetches relevant job postings based on user preferences
- Provides personalized recommendations for resume improvements
- Manages user authentication and data storage

### Two Implementations

**1. Server-Based Architecture (Django/AWS EC2)**
- **Tech Stack**: Django, PostgreSQL, Nginx, Gunicorn
- **AWS Services**: EC2, RDS, Route 53, VPC
- **Cost**: ~$95/month (24/7 operation)
- **Deployment**: CI/CD with GitHub Actions

**2. Serverless Architecture (AWS Lambda)**
- **Tech Stack**: Python, JavaScript, HTML/CSS
- **AWS Services**: Lambda, API Gateway, DynamoDB, S3, CloudFront, Cognito
- **Cost**: $0.43/month (pay-per-use)
- **Deployment**: AWS CLI + PowerShell scripts

## Key Findings

### Development Complexity
- **Server-based**: Django framework simplified feature implementation
- **Serverless**: Required extensive AWS service configuration and integration testing
- **Winner**: Server-based (faster development, easier debugging)

### Deployment Process
- **Server-based**: Complex initial setup, but automated CI/CD thereafter
- **Serverless**: Manual configuration for each service, simpler static file updates
- **Winner**: Tie (different trade-offs)

### Cost-Effectiveness
- **Server-based**: Fixed $95/month regardless of traffic
- **Serverless**: $0.43/month with variable, low traffic
- **Winner**: Serverless (99% cost reduction)

### Maintenance Requirements
- **Server-based**: OS patches, dependency updates, server monitoring
- **Serverless**: Minimal server maintenance, focus on Lambda logs
- **Winner**: Serverless (significantly less operational overhead)

### Scalability
- **Server-based**: Manual scaling, requires configuration
- **Serverless**: Automatic scaling built-in
- **Winner**: Serverless (inherent auto-scaling)

## Cost Breakdown (7-Month Period)

### Server-Based Architecture ($568.77 total)
| Service | Cost | Percentage | Purpose |
|---------|------|------------|---------|
| RDS | $211.01 | 37.1% | PostgreSQL database |
| EC2-Other | $164.31 | 28.9% | Data transfer, storage |
| VPC | $97.38 | 17.1% | Network infrastructure |
| EC2-Instances | $32.31 | 5.7% | Virtual server |
| Domain | $32.00 | 5.6% | resume-analyzer.net |

### Serverless Architecture ($0.43 total)
| Service | Cost | Percentage | Purpose |
|---------|------|------------|---------|
| S3 | $0.43 | 99.5% | Static website hosting |
| API Gateway | $0.001925 | 0.4% | REST API endpoints |
| DynamoDB | $0.000058 | 0.01% | NoSQL database |
| Lambda | $0.00 | 0% | Compute (free tier) |
| Cognito | $0.00 | 0% | Authentication (free tier) |

## Technology Stack

### Server-Based
- **Framework**: Django 
- **Database**: PostgreSQL (RDS)
- **Web Server**: Nginx + Gunicorn
- **Deployment**: GitHub Actions CI/CD
- **Infrastructure**: EC2, VPC, Route 53
- **Security**: Let's Encrypt SSL/TLS

### Serverless
- **Functions**: AWS Lambda (Python)
- **API**: API Gateway (REST)
- **Database**: DynamoDB (NoSQL)
- **Storage**: S3 + CloudFront (CDN)
- **Auth**: Cognito User Pools
- **Deployment**: AWS CLI + PowerShell

## Architecture Diagrams

### Server-Based Flow
```
User → Route 53 (DNS) → Internet Gateway → VPC 
  → Public Subnet → EC2 (Nginx/Django) 
  → Private Subnet → RDS (PostgreSQL)
```

### Serverless Flow
```
User → CloudFront (CDN) → S3 (Static Files)
  → API Gateway → Lambda Functions → DynamoDB
  → Cognito (Authentication)
```

## Software Development Lifecycle Comparison

| Phase | Server-Based | Serverless |
|-------|-------------|------------|
| **Planning** | Framework selection | AWS service architecture |
| **Design** | Django apps architecture | Event-driven design |
| **Development** | Python/Django, Git | Python functions, AWS Console |
| **Testing** | Django unit tests | Lambda unit tests, manual testing |
| **Deployment** | GitHub Actions automation | AWS CLI + scripts |
| **Maintenance** | OS/dependency updates | Lambda monitoring, minimal |

## Conclusions

### When to Use Server-Based
- **Predictable, sustained traffic** (constant usage justifies fixed costs)
- **Complex, monolithic applications** (Django framework advantages)
- **Team familiar with traditional web development**
- **Long-running computational tasks**
- **Strong relational database requirements**

### When to Use Serverless
- **Variable or sporadic traffic** (massive cost savings)
- **Microservices architecture** (independent function scaling)
- **Minimal operational overhead desired**
- **Rapid prototyping and iteration**
- **Cost-sensitive projects**
- **Event-driven workflows**

### Key Insight
**This research contradicts Deloitte's 2019 findings** that serverless reduces development effort. For this project, server-based architecture using Django proved faster to develop due to framework conveniences, while serverless required extensive manual configuration of AWS services.

## Related Work

This thesis builds upon:
- **Deloitte (2019)**: TCO framework comparing architectures
- **ElGazzar et al. (2025)**: MERN stack comparison on AWS
- **Amman (2025)**: Multi-dimensional comparative analysis

## Repository Contents

```
/server-based/
  - Django application code
  - GitHub Actions workflows
  - Infrastructure documentation

/serverless/
  - Lambda function code
  - API Gateway configurations
  - Deployment scripts
  - CloudFormation/SAM templates
```

## Future Work

- **Robust CI/CD Pipeline**: Implement comprehensive testing environments
- **Performance Benchmarking**: Load testing under varying traffic patterns
- **Security Hardening**: Enhanced security testing and compliance
- **Multi-region Deployment**: Geographic distribution analysis
- **Hybrid Architecture**: Combining benefits of both approaches

## Academic Context

- **Institution**: Bridgewater State University
- **Program**: Undergraduate Honors Program, Computer Science
- **Advisor**: Dr. John Santore
- **Committee**: Dr. Paul Kim, Dr. Seikyung Jung
- **Date**: 2025

## Key Metrics Summary

| Metric | Server-Based | Serverless | Winner |
|--------|-------------|------------|--------|
| **Monthly Cost** | $95 | $0.43 | Serverless (99% reduction) |
| **Development Time** | Faster | Slower | Server-Based |
| **Deployment Complexity** | Medium-High | High | Tie |
| **Maintenance Overhead** | High | Low | Serverless |
| **Scalability** | Manual | Automatic | Serverless |
| **Developer Experience** | Familiar | Steep learning curve | Server-Based |

## Acknowledgments

Special thanks to:
- Dr. John Santore (Thesis Advisor)
- Dr. Paul Kim (Committee Member)
- Dr. Seikyung Jung (Committee Member)
- Bridgewater State University Honors Program

## License

This is an academic research project for educational purposes.

---

**For detailed technical documentation, architectural diagrams, and complete cost analysis, please refer to the full thesis document.**