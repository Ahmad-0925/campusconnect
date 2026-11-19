param([string]$base = "http://localhost:8000")

function Call($method, $path, $body = $null, $token = $null) {
  $h = @{}
  if ($token) { $h["Authorization"] = "Bearer $token" }
  $script:last = @{ code = 200; err = "" }
  try {
    if ($body) {
      $r = Invoke-RestMethod -Method $method -Uri "$base$path" -Headers $h -ContentType "application/json" -Body ($body | ConvertTo-Json)
    } else {
      $r = Invoke-RestMethod -Method $method -Uri "$base$path" -Headers $h
    }
    return @{ code = 200; data = $r }
  } catch {
    $code = 0
    if ($_.Exception.Response) { $code = [int]$_.Exception.Response.StatusCode }
    $script:last = @{ code = $code; err = "$($_.ErrorDetails.Message)" }
    return @{ code = $code; data = $null }
  }
}

function Check($name, $ok) {
  if ($ok) {
    Write-Host "PASS  $name" -ForegroundColor Green
  } else {
    Write-Host "FAIL  $name" -ForegroundColor Red
    Write-Host "      -> last HTTP $($script:last.code) $($script:last.err)" -ForegroundColor Yellow
  }
}

Write-Host "Testing $base`n"

# 1. health
$r = Call GET "/"
Check "Server health" ($r.code -eq 200 -and $r.data.status -eq "ok")

# 2. admin logins
$tok = @{}
foreach ($pair in @(
  @("super@biit.edu","super_admin"),
  @("cafeteria@biit.edu","dept_admin"),
  @("library@biit.edu","dept_admin"),
  @("lab@biit.edu","dept_admin"),
  @("academic@biit.edu","dept_admin"))) {
  $r = Call POST "/auth/login" @{ email = $pair[0]; password = "admin123" }
  Check "Login $($pair[0])" ($r.code -eq 200 -and $r.data.user.role -eq $pair[1])
  if ($r.code -eq 200) { $tok[$pair[0]] = $r.data.access_token }
}

# 3. bad password
$r = Call POST "/auth/login" @{ email = "super@biit.edu"; password = "wrong" }
Check "Wrong password rejected (401)" ($r.code -eq 401)

# 4. register student
$email = "student$(Get-Random)@test.com"
$r = Call POST "/auth/register" @{ name = "Test Student"; email = $email; password = "123456" }
Check "Student registration" ($r.code -eq 200 -and $r.data.user.role -eq "student")
$st = $r.data.access_token

# 5. duplicate email
$r = Call POST "/auth/register" @{ name = "Test Student"; email = $email; password = "123456" }
Check "Duplicate email rejected (400)" ($r.code -eq 400)

# 6. categories
$r = Call GET "/complaints/categories" $null $st
Check "16 categories returned" (@($r.data).Count -eq 16)

# 7. submit complaint + auto routing
$r = Call POST "/complaints" @{ category = "Library - Timings"; title = "Library closes early"; description = "The library closes at 4 PM during exams." } $st
Check "Complaint created and routed to Library" ($r.code -eq 200 -and $r.data.department -eq "Library" -and $r.data.status -eq "pending")
$cid = $r.data.id
Write-Host "      (complaint id: $cid)" -ForegroundColor DarkGray

$r = Call POST "/complaints" @{ category = "Lab/IT - Internet Connectivity"; title = "WiFi down in lab 2"; description = "No internet in computer lab 2 since morning." } $st
Check "Internet complaint routed to Laboratory/IT" ($r.code -eq 200 -and $r.data.department -eq "Laboratory/IT")

# 8. student sees own
$r = Call GET "/complaints/mine" $null $st
Check "Student sees own complaints" (@($r.data).Count -ge 2)

# 9. no token / student blocked from admin
$r = Call GET "/admin/complaints"
Check "No token blocked (401/403)" ($r.code -eq 401 -or $r.code -eq 403)
$r = Call GET "/admin/complaints" $null $st
Check "Student blocked from admin list (403)" ($r.code -eq 403)

# 10. dept isolation: Lab admin vs Library complaint
$labTok = $tok["lab@biit.edu"]
$r = Call GET "/admin/complaints" $null $labTok
$leak = @($r.data | Where-Object { $_.department -ne "Laboratory/IT" }).Count
Check "Lab admin list contains only Lab complaints" ($r.code -eq 200 -and $leak -eq 0)
$r = Call GET "/complaints/$cid" $null $labTok
Check "Lab admin blocked from Library complaint by direct URL (403)" ($r.code -eq 403)
$r = Call PATCH "/admin/complaints/$cid" @{ status = "in_progress" } $labTok
Check "Lab admin cannot update Library complaint (403)" ($r.code -eq 403)

# 11. Library admin manages own
$libTok = $tok["library@biit.edu"]
$r = Call GET "/admin/complaints" $null $libTok
Check "Library admin sees the complaint" (@($r.data | Where-Object { $_.id -eq $cid }).Count -eq 1)
$r = Call PATCH "/admin/complaints/$cid" @{ status = "in_progress" } $libTok
Check "Library admin sets in_progress" ($r.code -eq 200 -and $r.data.status -eq "in_progress")
$r = Call PATCH "/admin/complaints/$cid" @{ status = "resolved" } $libTok
Check "Resolve without remarks rejected (400)" ($r.code -eq 400)
$r = Call PATCH "/admin/complaints/$cid" @{ status = "resolved"; remarks = "Hours extended to 8 PM" } $libTok
Check "Library admin resolves with remarks" ($r.code -eq 200 -and $r.data.status -eq "resolved")

# 12. student sees remarks
$r = Call GET "/complaints/$cid" $null $st
Check "Student sees status + remarks" ($r.code -eq 200 -and $r.data.status -eq "resolved" -and $r.data.remarks -like "Hours*")

# 13. stats
$r = Call GET "/admin/stats" $null $tok["super@biit.edu"]
Check "Super admin stats (all departments)" ($r.code -eq 200 -and $r.data.total -ge 2)
$r = Call GET "/admin/stats" $null $libTok
Check "Library admin stats scoped to Library" ($r.code -eq 200 -and $r.data.scope -eq "Library")

# 14. super admin filters
$r = Call GET "/admin/complaints?department=Library&status=resolved" $null $tok["super@biit.edu"]
Check "Super admin filter works" ($r.code -eq 200 -and @($r.data).Count -ge 1)

Write-Host "`nDone."