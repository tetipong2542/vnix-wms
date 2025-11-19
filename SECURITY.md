# Security Guide

## ✅ Security Improvements Implemented

### 1. Environment-Based Configuration
- ✅ SECRET_KEY now required from `.env` file (no hardcoded fallback)
- ✅ Random admin password generated on first run
- ✅ Sensitive data in `.env` (excluded from git)

### 2. Database Backups
- ✅ Automated backup script (`backup_database.sh`)
- ✅ Backups kept for 30 days
- ✅ Database integrity checks before backup

## 🔒 Security Checklist

### Initial Setup

1. **Create `.env` file**:
   ```bash
   cp .env.example .env
   ```

2. **Generate SECRET_KEY**:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   Add to `.env`:
   ```
   SECRET_KEY=your-generated-key-here
   ```

3. **Start the application**:
   ```bash
   python app.py
   ```
   - If no users exist, a random admin password will be generated
   - **Important**: Save the password shown in console!

4. **Change admin password**:
   - Login with generated password
   - Go to user settings and change password immediately

### Production Deployment

1. **Never commit `.env` file**:
   - ✅ Already in `.gitignore`
   - Double-check before committing

2. **Use strong SECRET_KEY**:
   - Minimum 32 characters
   - Random hex string
   - Different for each environment (dev/staging/prod)

3. **Setup automated backups**:
   ```bash
   ./setup_cron.sh
   ```
   This creates backups every 6 hours

4. **Secure the server**:
   - Use HTTPS (SSL/TLS)
   - Firewall configuration
   - Regular OS updates
   - Limit SSH access

5. **Database security**:
   - Set file permissions: `chmod 600 data.db`
   - Backup folder permissions: `chmod 700 backups/`
   - Regular integrity checks

### Password Policy

**For admin/users**:
- Minimum 8 characters
- Mix of letters, numbers, symbols
- Change every 90 days
- Don't reuse old passwords

### Access Control

**User Roles**:
- `admin`: Full access
- `warehouse`: Picking/scanning operations
- `viewer`: Read-only access

**Session Security**:
- Session timeout: 8 hours (480 minutes)
- Auto-logout on browser close
- CSRF protection (if using forms)

## 🚨 Security Incidents

### If you suspect a security breach:

1. **Immediate actions**:
   - Change SECRET_KEY in `.env`
   - Restart application
   - Check `audit_logs` table for suspicious activity

2. **Password reset**:
   ```sql
   -- Reset user password (run in sqlite3)
   UPDATE users SET password_hash = 'new_hash' WHERE username = 'username';
   ```

3. **Review logs**:
   ```bash
   tail -f server.log
   grep "ERROR" server.log
   ```

4. **Check recent changes**:
   ```sql
   SELECT * FROM audit_logs
   ORDER BY timestamp DESC
   LIMIT 50;
   ```

## 📋 Regular Security Tasks

### Daily
- Review backup logs (`tail backup.log`)
- Check application logs for errors

### Weekly
- Review user activity in audit_logs
- Check disk space for backups

### Monthly
- Test backup restore procedure
- Review user accounts (disable inactive)
- Update dependencies: `pip install -r requirements.txt --upgrade`

### Quarterly
- Change SECRET_KEY
- Security audit of audit_logs
- Review and update this document

## 🔧 Hardening Recommendations

### Application Level
1. Rate limiting on login (prevent brute force)
2. IP whitelist for admin panel
3. Two-factor authentication (2FA)
4. API authentication tokens

### Database Level
1. Enable WAL mode: `PRAGMA journal_mode=WAL;`
2. Regular VACUUM operations
3. Foreign key constraints enabled

### Server Level
1. Run as non-root user
2. Use reverse proxy (nginx/apache)
3. Setup fail2ban for SSH
4. Enable UFW firewall

## 📞 Security Contacts

If you discover a security vulnerability:
1. Do NOT create a public GitHub issue
2. Contact: [Your contact email]
3. Provide details: version, steps to reproduce, impact

## 🔐 Compliance Notes

This system handles:
- Order data (may contain customer information)
- Inventory data
- User credentials

Ensure compliance with:
- PDPA (Personal Data Protection Act) - Thailand
- Your company's data retention policies
- Industry-specific regulations

## 📚 References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security](https://flask.palletsprojects.com/en/latest/security/)
- [SQLite Security](https://www.sqlite.org/security.html)

---

**Last Updated**: 2025-11-19
**Version**: 1.0
