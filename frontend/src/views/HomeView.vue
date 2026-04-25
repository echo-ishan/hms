<template>
  <section class="home-wrap">
    <article class="home-hero card">
      <p class="eyebrow">Hospital Management System</p>
      <h1>Care coordination in one clean workspace.</h1>
      <p class="hero-copy">
        Manage appointments, doctors, departments, and patient records with a fast role-based workflow.
      </p>
      <div class="hero-actions">
        <RouterLink to="/login" class="btn primary">Sign In</RouterLink>
        <RouterLink to="/register" class="btn">Create Patient Account</RouterLink>
      </div>
    </article>

    <section class="role-grid" aria-label="Role access">
      <article class="card role-card">
        <h3>Patient</h3>
        <p class="muted">Book visits, track appointments, and review treatment history.</p>
        <RouterLink to="/patient/dashboard" class="btn small">Open Patient Dashboard</RouterLink>
      </article>

      <article class="card role-card">
        <h3>Doctor</h3>
        <p class="muted">Manage schedule, update treatment plans, and follow-up records.</p>
        <RouterLink to="/doctor/dashboard" class="btn small">Open Doctor Dashboard</RouterLink>
      </article>

      <article class="card role-card">
        <h3>Admin</h3>
        <p class="muted">Maintain doctors, patients, departments, and appointments.</p>
        <RouterLink to="/admin/dashboard" class="btn small">Open Admin Dashboard</RouterLink>
      </article>
    </section>
  </section>
</template>

<style scoped>
.home-wrap {
  display: grid;
  gap: 1rem;
}

.home-hero {
  display: grid;
  gap: 0.8rem;
  background: linear-gradient(120deg, #f9fcff 0%, #edf5fb 100%);
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--color-primary);
}

h1 {
  font-size: clamp(1.6rem, 2.8vw, 2.1rem);
  line-height: 1.2;
}

.hero-copy {
  color: var(--color-text-secondary);
  max-width: 68ch;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}

.role-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
}

.role-card {
  display: grid;
  gap: 0.7rem;
}

.role-card h3 {
  font-size: 1.05rem;
}

@media (max-width: 980px) {
  .role-grid {
    grid-template-columns: 1fr;
  }
}
</style>
