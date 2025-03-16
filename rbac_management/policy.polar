# Base rule: a user can perform an action on a resource if they have a permission for it
allow(user: User, action, resource) if
    has_permission(user, action, resource);

# A user has permission if they have a permission with matching action and resource
has_permission(user: User, action, resource) if
    permission in user.permissions and
    permission.action = action and
    permission.resource = resource;

# Superadmin can do anything
allow(user: User, _action, _resource) if
    has_role(user, "superadmin");

# Check if user has a specific role
has_role(user: User, role_name) if
    role in user.roles and
    role.name = role_name;

# Modified rule - use a variable to capture the role
allow(user: User, action, resource) if
    role = user.role and  # Assign to variable instead of using as condition
    permission in role.permissions and
    permission.action = action and
    permission.resource = resource.name;


# Alternative approach if role might be null
allow(user: User, action, resource) if
    # Check if user has a direct role-based permission
    user.role != null and  # Explicit null check
    permission in user.role.permissions and
    permission.action = action and
    permission.resource = resource.name;


# Modified rule - use a variable to capture the role
allow(user: User, action, resource) if
    role = user.role and  # Assign to variable instead of using as condition
    permission in role.permissions and
    permission.action = action and
    permission.resource = resource.name;