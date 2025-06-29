<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-medium text-gray-900">User Management</h3>
      <div class="flex space-x-2">
        <button 
          @click="showBulkOperationsModal = true"
          class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
        >
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
          </svg>
          Bulk Operations
        </button>
        <button 
          @click="$emit('refresh')"
          class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
        >
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
          </svg>
          Refresh
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white p-4 rounded-lg shadow">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Role Filter</label>
          <select v-model="filters.role" @change="applyFilters" class="w-full rounded-md border border-gray-300 bg-white py-2 px-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-150">
            <option value="">All Roles</option>
            <option value="admin">Admin</option>
            <option value="risk_officer">Risk Officer</option>
            <option value="loan_officer">Loan Officer</option>
            <option value="support">Support</option>
            <option value="customer">Customer</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Status Filter</label>
          <select v-model="filters.status" @change="applyFilters" class="w-full rounded-md border border-gray-300 bg-white py-2 px-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-150">
            <option value="">All Statuses</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="locked">Locked</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">State Filter</label>
          <select v-model="filters.state" @change="applyFilters" class="w-full rounded-md border border-gray-300 bg-white py-2 px-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-150">
            <option value="">All States</option>
            <option value="registered">Registered</option>
            <option value="onboarding">Onboarding</option>
            <option value="onboarded">Onboarded</option>
            <option value="suspended">Suspended</option>
            <option value="outdated">Outdated</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Search</label>
          <input 
            v-model="filters.search" 
            @input="applyFilters"
            type="text" 
            placeholder="Name, email, username..."
            class="w-full rounded-md border-gray-300 text-sm"
          >
        </div>
      </div>
    </div>

    <div v-if="filteredUsers.length > 0" class="bg-white shadow overflow-hidden sm:rounded-md">
      <ul class="divide-y divide-gray-200">
        <li v-for="user in filteredUsers" :key="user.id" class="px-6 py-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <div class="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                  <span class="text-sm font-medium text-gray-700">
                    {{ user.first_name?.charAt(0) }}{{ user.last_name?.charAt(0) }}
                  </span>
                </div>
              </div>
              <div class="ml-4">
                <div class="text-sm font-medium text-gray-900">
                  {{ user.first_name }} {{ user.last_name }}
                </div>
                <div class="text-sm text-gray-500">
                  {{ user.email }}
                </div>
                <div class="text-xs text-gray-400">
                  @{{ user.username }}
                </div>
                <div class="flex items-center space-x-2 mt-1">
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                        :class="getRoleBadgeClass(user.role)">
                    {{ formatRole(user.role) }}
                  </span>
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                        :class="getStatusBadgeClass(user.is_active)">
                    {{ user.is_active ? 'Active' : 'Inactive' }}
                  </span>
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                        :class="getStateBadgeClass(user.user_state)">
                    {{ formatState(user.user_state) }}
                  </span>
                </div>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <span class="text-sm text-gray-500">
                Last login: {{ formatDate(user.last_login) }}
              </span>
              <div class="flex space-x-1">
                <button 
                  v-if="isAdmin"
                  @click="viewUserDetails(user)"
                  class="text-blue-600 hover:text-blue-900 text-sm font-medium px-2 py-1 rounded hover:bg-blue-50"
                  title="View Details"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                  </svg>
                </button>
                <button 
                  v-if="isAdmin"
                  @click="editUserRole(user)"
                  class="text-green-600 hover:text-green-900 text-sm font-medium px-2 py-1 rounded hover:bg-green-50"
                  :disabled="user.role === 'admin' && currentUserId === user.id"
                  :title="user.role === 'admin' && currentUserId === user.id ? 'Cannot change your own role' : 'Change Role'"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                  </svg>
                </button>
                <button 
                  v-if="isAdmin"
                  @click="editUserState(user)"
                  class="text-orange-600 hover:text-orange-900 text-sm font-medium px-2 py-1 rounded hover:bg-orange-50"
                  title="Change State"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                  </svg>
                </button>
                <button 
                  v-if="isAdmin"
                  @click="$emit('delete', user.id)"
                  class="text-red-600 hover:text-red-900 text-sm font-medium px-2 py-1 rounded hover:bg-red-50"
                  :disabled="user.role === 'admin'"
                  :title="user.role === 'admin' ? 'Cannot delete admin users' : 'Delete user'"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </li>
      </ul>
    </div>

    <!-- Empty State -->
    <div v-else class="text-center py-12">
      <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"/>
      </svg>
      <h3 class="mt-4 text-lg font-medium text-gray-900">No users found</h3>
      <p class="mt-2 text-gray-500">{{ filters.search || filters.role || filters.status || filters.state ? 'No users match your filters.' : 'No users are currently registered in the system.' }}</p>
    </div>

    <!-- Loading State -->
    <div v-if="!users && users.length === 0" class="text-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
      <p class="mt-2 text-sm text-gray-500">Loading users...</p>
    </div>

    <!-- User Details Modal -->
    <div v-if="showUserDetailsModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
      <div class="relative mx-auto p-5 border w-full max-w-4xl shadow-lg rounded-md bg-white">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-medium text-gray-900">User Details</h3>
          <button @click="closeUserDetailsModal" class="text-gray-400 hover:text-gray-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        
        <div v-if="selectedUserDetails" class="space-y-6">
          <!-- Basic Info -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 class="text-sm font-medium text-gray-900 mb-3">Basic Information</h4>
              <dl class="space-y-2">
                <div>
                  <dt class="text-sm font-medium text-gray-500">Full Name</dt>
                  <dd class="text-sm text-gray-900">{{ selectedUserDetails.first_name }} {{ selectedUserDetails.last_name }}</dd>
                </div>
                <div>
                  <dt class="text-sm font-medium text-gray-500">Email</dt>
                  <dd class="text-sm text-gray-900">{{ selectedUserDetails.email }}</dd>
                </div>
                <div>
                  <dt class="text-sm font-medium text-gray-500">Username</dt>
                  <dd class="text-sm text-gray-900">{{ selectedUserDetails.username }}</dd>
                </div>
                <div>
                  <dt class="text-sm font-medium text-gray-500">Phone</dt>
                  <dd class="text-sm text-gray-900">{{ selectedUserDetails.phone_number || 'Not provided' }}</dd>
                </div>
              </dl>
            </div>
            
            <div>
              <h4 class="text-sm font-medium text-gray-900 mb-3">Account Status</h4>
              <dl class="space-y-2">
                <div>
                  <dt class="text-sm font-medium text-gray-500">Role</dt>
                  <dd class="text-sm">
                    <span :class="getRoleBadgeClass(selectedUserDetails.role)">
                      {{ formatRole(selectedUserDetails.role) }}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt class="text-sm font-medium text-gray-500">State</dt>
                  <dd class="text-sm">
                    <span :class="getStateBadgeClass(selectedUserDetails.user_state)">
                      {{ formatState(selectedUserDetails.user_state) }}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt class="text-sm font-medium text-gray-500">Status</dt>
                  <dd class="text-sm">
                    <span :class="getStatusBadgeClass(selectedUserDetails.is_active)">
                      {{ selectedUserDetails.is_active ? 'Active' : 'Inactive' }}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt class="text-sm font-medium text-gray-500">Verified</dt>
                  <dd class="text-sm text-gray-900">{{ selectedUserDetails.is_verified ? 'Yes' : 'No' }}</dd>
                </div>
                <div>
                  <dt class="text-sm font-medium text-gray-500">Locked</dt>
                  <dd class="text-sm text-gray-900">{{ selectedUserDetails.is_locked ? 'Yes' : 'No' }}</dd>
                </div>
              </dl>
            </div>
          </div>

          <!-- Activity Info -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 class="text-sm font-medium text-gray-900 mb-3">Activity Information</h4>
              <dl class="space-y-2">
                <div>
                  <dt class="text-sm font-medium text-gray-500">Last Login</dt>
                  <dd class="text-sm text-gray-900">{{ formatDate(selectedUserDetails.last_login) }}</dd>
                </div>
                <div>
                  <dt class="text-sm font-medium text-gray-500">Created</dt>
                  <dd class="text-sm text-gray-900">{{ formatDate(selectedUserDetails.created_at) }}</dd>
                </div>
                <div>
                  <dt class="text-sm font-medium text-gray-500">Onboarding Completed</dt>
                  <dd class="text-sm text-gray-900">{{ formatDate(selectedUserDetails.onboarding_completed_at) }}</dd>
                </div>
                <div>
                  <dt class="text-sm font-medium text-gray-500">Last Profile Update</dt>
                  <dd class="text-sm text-gray-900">{{ formatDate(selectedUserDetails.last_profile_update) }}</dd>
                </div>
                <div>
                  <dt class="text-sm font-medium text-gray-500">Profile Expiry</dt>
                  <dd class="text-sm text-gray-900">{{ formatDate(selectedUserDetails.profile_expiry_date) }}</dd>
                </div>
              </dl>
            </div>
            
            <div>
              <h4 class="text-sm font-medium text-gray-900 mb-3">Application Statistics</h4>
              <dl class="space-y-2">
                <div>
                  <dt class="text-sm font-medium text-gray-500">Total Applications</dt>
                  <dd class="text-sm text-gray-900">{{ selectedUserDetails.total_applications || 0 }}</dd>
                </div>
                <div>
                  <dt class="text-sm font-medium text-gray-500">Approved</dt>
                  <dd class="text-sm text-gray-900">{{ selectedUserDetails.approved_applications || 0 }}</dd>
                </div>
                <div>
                  <dt class="text-sm font-medium text-gray-500">Rejected</dt>
                  <dd class="text-sm text-gray-900">{{ selectedUserDetails.rejected_applications || 0 }}</dd>
                </div>
                <div>
                  <dt class="text-sm font-medium text-gray-500">Pending</dt>
                  <dd class="text-sm text-gray-900">{{ selectedUserDetails.pending_applications || 0 }}</dd>
                </div>
                <div>
                  <dt class="text-sm font-medium text-gray-500">Profile Completion</dt>
                  <dd class="text-sm text-gray-900">{{ selectedUserDetails.profile_completion_percentage || 0 }}%</dd>
                </div>
              </dl>
            </div>
          </div>

          <!-- Role History -->
          <div v-if="selectedUserDetails.role_history && selectedUserDetails.role_history.length > 0">
            <h4 class="text-sm font-medium text-gray-900 mb-3">Role History</h4>
            <div class="bg-gray-50 rounded-lg p-4">
              <div v-for="history in selectedUserDetails.role_history" :key="history.id" class="border-b border-gray-200 last:border-b-0 py-2">
                <div class="flex justify-between items-start">
                  <div>
                    <span class="text-sm font-medium">{{ formatRole(history.old_role) }} → {{ formatRole(history.new_role) }}</span>
                    <p class="text-xs text-gray-500">{{ history.reason }}</p>
                  </div>
                  <div class="text-right">
                    <p class="text-xs text-gray-500">{{ formatDate(history.changed_at) }}</p>
                    <p v-if="history.changed_by_name" class="text-xs text-gray-500">by {{ history.changed_by_name }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Role Change Modal -->
    <div v-if="showRoleModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
      <div class="relative mx-auto p-5 border w-full max-w-md shadow-lg rounded-md bg-white">
        <h3 class="text-lg font-medium text-gray-900 mb-4">Change User Role</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">User</label>
            <p class="text-sm text-gray-900">{{ selectedUserForRole?.first_name }} {{ selectedUserForRole?.last_name }} ({{ selectedUserForRole?.email }})</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Current Role</label>
            <span :class="getRoleBadgeClass(selectedUserForRole?.role)">
              {{ formatRole(selectedUserForRole?.role) }}
            </span>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">New Role</label>
            <select v-model="roleUpdateForm.newRole" class="w-full rounded-md border border-gray-300 bg-white py-2 px-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-150">
              <option value="">Select new role</option>
              <option value="admin">Admin</option>
              <option value="risk_officer">Risk Officer</option>
              <option value="loan_officer">Loan Officer</option>
              <option value="support">Support</option>
              <option value="customer">Customer</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Reason</label>
            <textarea v-model="roleUpdateForm.reason" class="w-full rounded-md border-gray-300" rows="3" placeholder="Reason for role change..."></textarea>
          </div>
        </div>
        <div class="flex space-x-3 mt-6">
          <button @click="updateUserRole" :disabled="!roleUpdateForm.newRole || !roleUpdateForm.reason" class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400">Update Role</button>
          <button @click="closeRoleModal" class="flex-1 px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50">Cancel</button>
        </div>
      </div>
    </div>

    <!-- State Change Modal -->
    <div v-if="showStateModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
      <div class="relative mx-auto p-5 border w-full max-w-md shadow-lg rounded-md bg-white">
        <h3 class="text-lg font-medium text-gray-900 mb-4">Change User State</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">User</label>
            <p class="text-sm text-gray-900">{{ selectedUserForState?.first_name }} {{ selectedUserForState?.last_name }} ({{ selectedUserForState?.email }})</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Current State</label>
            <span :class="getStateBadgeClass(selectedUserForState?.user_state)">
              {{ formatState(selectedUserForState?.user_state) }}
            </span>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">New State</label>
            <select v-model="stateUpdateForm.newState" class="w-full rounded-md border border-gray-300 bg-white py-2 px-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-150">
              <option value="">Select new state</option>
              <option value="registered">Registered</option>
              <option value="onboarding">Onboarding</option>
              <option value="onboarded">Onboarded</option>
              <option value="suspended">Suspended</option>
              <option value="outdated">Outdated</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Reason</label>
            <textarea v-model="stateUpdateForm.reason" class="w-full rounded-md border-gray-300" rows="3" placeholder="Reason for state change..."></textarea>
          </div>
        </div>
        <div class="flex space-x-3 mt-6">
          <button @click="updateUserState" :disabled="!stateUpdateForm.newState || !stateUpdateForm.reason" class="flex-1 px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 disabled:bg-gray-400">Update State</button>
          <button @click="closeStateModal" class="flex-1 px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50">Cancel</button>
        </div>
      </div>
    </div>

    <!-- Bulk Operations Modal -->
    <div v-if="showBulkOperationsModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
      <div class="relative mx-auto p-5 border w-full max-w-md shadow-lg rounded-md bg-white">
        <h3 class="text-lg font-medium text-gray-900 mb-4">Bulk Operations</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Select Users</label>
            <div class="max-h-40 overflow-y-auto border border-gray-300 rounded-md p-2">
              <label v-for="user in users" :key="user.id" class="flex items-center space-x-2 py-1">
                <input type="checkbox" v-model="bulkOperationsForm.selectedUsers" :value="user.id" class="rounded border-gray-300">
                <span class="text-sm">{{ user.first_name }} {{ user.last_name }} ({{ user.email }})</span>
              </label>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Operation</label>
            <select v-model="bulkOperationsForm.operation" class="w-full rounded-md border border-gray-300 bg-white py-2 px-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-150">
              <option value="">Select operation</option>
              <option value="activate">Activate</option>
              <option value="deactivate">Deactivate</option>
              <option value="verify">Verify</option>
              <option value="lock">Lock</option>
              <option value="unlock">Unlock</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Reason</label>
            <textarea v-model="bulkOperationsForm.reason" class="w-full rounded-md border-gray-300" rows="3" placeholder="Reason for bulk operation..."></textarea>
          </div>
        </div>
        <div class="flex space-x-3 mt-6">
          <button @click="performBulkOperation" :disabled="!bulkOperationsForm.selectedUsers.length || !bulkOperationsForm.operation || !bulkOperationsForm.reason" class="flex-1 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:bg-gray-400">Perform Operation</button>
          <button @click="closeBulkOperationsModal" class="flex-1 px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50">Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import api from '@/services/api'

const props = defineProps({
  users: {
    type: Array,
    default: () => []
  },
  isAdmin: {
    type: Boolean,
    default: false
  },
  currentUserId: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['refresh', 'delete'])

// Reactive state
const filters = ref({
  role: '',
  status: '',
  state: '',
  search: ''
})

const showUserDetailsModal = ref(false)
const showRoleModal = ref(false)
const showStateModal = ref(false)
const showBulkOperationsModal = ref(false)

const selectedUserDetails = ref(null)
const selectedUserForRole = ref(null)
const selectedUserForState = ref(null)

const roleUpdateForm = ref({
  newRole: '',
  reason: ''
})

const stateUpdateForm = ref({
  newState: '',
  reason: ''
})

const bulkOperationsForm = ref({
  selectedUsers: [],
  operation: '',
  reason: ''
})

// Computed properties
const filteredUsers = computed(() => {
  let filtered = props.users

  if (filters.value.role) {
    filtered = filtered.filter(user => user.role === filters.value.role)
  }

  if (filters.value.status) {
    if (filters.value.status === 'active') {
      filtered = filtered.filter(user => user.is_active)
    } else if (filters.value.status === 'inactive') {
      filtered = filtered.filter(user => !user.is_active)
    } else if (filters.value.status === 'locked') {
      filtered = filtered.filter(user => user.is_locked)
    }
  }

  if (filters.value.state) {
    filtered = filtered.filter(user => 
      user.user_state?.toLowerCase() === filters.value.state.toLowerCase()
    )
  }

  if (filters.value.search) {
    const searchTerm = filters.value.search.toLowerCase()
    filtered = filtered.filter(user => 
      user.first_name?.toLowerCase().includes(searchTerm) ||
      user.last_name?.toLowerCase().includes(searchTerm) ||
      user.email?.toLowerCase().includes(searchTerm) ||
      user.username?.toLowerCase().includes(searchTerm)
    )
  }

  return filtered
})

// Methods
const applyFilters = () => {
  // Filters are applied automatically through computed property
}

const viewUserDetails = async (user) => {
  try {
    const response = await api.get(`/admin/users/${user.id}/profile`)
    selectedUserDetails.value = response.data
    showUserDetailsModal.value = true
  } catch (error) {
    console.error('Failed to load user details:', error)
    alert('Failed to load user details')
  }
}

const closeUserDetailsModal = () => {
  showUserDetailsModal.value = false
  selectedUserDetails.value = null
}

const editUserRole = (user) => {
  selectedUserForRole.value = user
  roleUpdateForm.value = {
    newRole: '',
    reason: ''
  }
  showRoleModal.value = true
}

const closeRoleModal = () => {
  showRoleModal.value = false
  selectedUserForRole.value = null
  roleUpdateForm.value = { newRole: '', reason: '' }
}

const updateUserRole = async () => {
  try {
    await api.put(`/admin/users/${selectedUserForRole.value.id}/role`, {
      new_role: roleUpdateForm.value.newRole,
      reason: roleUpdateForm.value.reason
    })
    
    alert('User role updated successfully')
    closeRoleModal()
    emit('refresh')
  } catch (error) {
    console.error('Failed to update user role:', error)
    alert(error.response?.data?.detail || 'Failed to update user role')
  }
}

const editUserState = (user) => {
  selectedUserForState.value = user
  stateUpdateForm.value = {
    newState: '',
    reason: ''
  }
  showStateModal.value = true
}

const closeStateModal = () => {
  showStateModal.value = false
  selectedUserForState.value = null
  stateUpdateForm.value = { newState: '', reason: '' }
}

const updateUserState = async () => {
  try {
    await api.put(`/admin/users/${selectedUserForState.value.id}/state`, {
      new_state: stateUpdateForm.value.newState,
      reason: stateUpdateForm.value.reason
    })
    
    alert('User state updated successfully')
    closeStateModal()
    emit('refresh')
  } catch (error) {
    console.error('Failed to update user state:', error)
    alert(error.response?.data?.detail || 'Failed to update user state')
  }
}

const closeBulkOperationsModal = () => {
  showBulkOperationsModal.value = false
  bulkOperationsForm.value = { selectedUsers: [], operation: '', reason: '' }
}

const performBulkOperation = async () => {
  try {
    await api.post('/admin/users/bulk-operations', {
      user_ids: bulkOperationsForm.value.selectedUsers,
      operation: bulkOperationsForm.value.operation,
      reason: bulkOperationsForm.value.reason
    })
    
    alert('Bulk operation completed successfully')
    closeBulkOperationsModal()
    emit('refresh')
  } catch (error) {
    console.error('Failed to perform bulk operation:', error)
    alert(error.response?.data?.detail || 'Failed to perform bulk operation')
  }
}

// Utility functions
const getRoleBadgeClass = (role) => {
  switch (role) {
    case 'admin':
      return 'bg-purple-100 text-purple-800'
    case 'loan_officer':
      return 'bg-blue-100 text-blue-800'
    case 'risk_officer':
      return 'bg-orange-100 text-orange-800'
    case 'support':
      return 'bg-yellow-100 text-yellow-800'
    case 'customer':
      return 'bg-green-100 text-green-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

const getStatusBadgeClass = (isActive) => {
  return isActive ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
}

const getStateBadgeClass = (state) => {
  switch (state) {
    case 'registered':
      return 'bg-gray-100 text-gray-800'
    case 'onboarding':
      return 'bg-blue-100 text-blue-800'
    case 'onboarded':
      return 'bg-green-100 text-green-800'
    case 'suspended':
      return 'bg-red-100 text-red-800'
    case 'outdated':
      return 'bg-yellow-100 text-yellow-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

const formatRole = (role) => {
  return role?.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ') || ''
}

const formatState = (state) => {
  return state?.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ') || ''
}

const formatDate = (dateString) => {
  if (!dateString) return 'Never'
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script> 