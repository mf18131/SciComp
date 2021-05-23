import numpy as np, types
import matplotlib.pyplot as plt
from math import pi, log2, e
import scipy as sp
import scipy.sparse
from scipy.sparse.linalg import spsolve
from sklearn.linear_model import LinearRegression
from scipy.optimize import root, fsolve


# Set problem parameters/functions
kappa = 1  # diffusion constant
# total time to solve for
def u_I(x):
    # initial temperature distribution
    # y = np.sin(pi*x/L)
    y = e**(-16*(x**2))
    return y


def u_fx(x):
    return x*(1 - x)


def u_exact(x, t):
    # the exact solution
    y = np.exp(-kappa*(pi**2/L**2)*t)*np.sin(pi*x/L)
    return y


def forward_euler_main(max_x, max_t, T, L, pde, bcs, bc_type=None, ):
    bc1 = bcs[0]
    bc2 = bcs[1]
    if type(bc1) != types.FunctionType or type(bc2) != types.FunctionType:
        raise TypeError('Both Boundary Conditions must be of type function (lambda or defined), even if 0')
    x = np.linspace(0, L, max_x+1)     # mesh points in space
    t = np.linspace(0, T, max_t+1)
    jarray = np.zeros(x.size)        # u at current time step
    jarray1 = np.zeros(x.size)

    #Calculate initial conditions
    for i in range(0, max_x+1):
        jarray[i] = pde(x[i])

    deltax = x[1] - x[0]            # gridspacing in x
    deltat = t[1] - t[0]            # gridspacing in t
    lmbda = kappa*deltat/(deltax**2)
    if lmbda >= 0.5:
        raise ValueError('Forward Euler is conditionally stable for lambda < 0.5, your lambda is:', lmbda)

    if bc_type == None:
        print("Please choose a boundary condition type")
        bc_type = input("dirichlet, or neumann")

    if bc_type == 'neumann':
        a = lmbda * np.ones(max_x+1)
        b = (1-2*lmbda)*np.ones(max_x+1)
        c = lmbda * np.ones(max_x+1)
        a[-2] = c[1] = 2*lmbda
        mtrx = np.array([a, b, c])
        pos = [-1, 0, 1]
        A_FE = sp.sparse.spdiags(mtrx, pos, max_x+1, max_x+1).todense()
        for j in range(max_t):
            #Matrix calculations
            b_array = np.zeros(jarray.size)
            b_array[0] = bc1(t[j])
            b_array[-1] = bc2(t[j])
            jarray1 = np.dot(A_FE, jarray) + 2*lmbda*deltax*b_array

            # Save u_j at time t[j+1]
            jarray[:] = jarray1[:]
        return x, jarray

    elif bc_type == 'dirichlet':
        a = lmbda * np.ones(max_x-1)
        b = (1-2*lmbda)*np.ones(max_x-1)
        c = a
        mtrx = np.array([a, b, c])
        pos = [-1, 0, 1]
        A_FE = sp.sparse.spdiags(mtrx, pos, max_x-1, max_x-1).todense()
        for j in range(max_t):
            #Matrix calculations
            b_array = np.zeros(jarray[1:-1].size)
            b_array[0] = bc1(t[j])
            b_array[-1] = bc2(t[j])
            jarray1[1:-1] = np.dot(A_FE, jarray[1:-1]) + lmbda*b_array
            # Set up BCs
            jarray1[0] = bc1(t[j])
            jarray1[max_x] = bc2(t[j])
            # Save u_j at time t[j+1]
            jarray[:] = jarray1[:]
        return x, jarray
    else:
        raise ValueError('Boundary conditions must be either dirichlet or neumann')


def backwards_euler_main(max_x, max_t, T, L, pde, bcs, bc_type=None):
    bc1 = bcs[0]
    bc2 = bcs[1]
    if type(bc1) != types.FunctionType or type(bc2) != types.FunctionType:
        raise TypeError('Both Boundary Conditions must be of type function (lambda or defined), even if 0')
    x = np.linspace(0, L, max_x+1)     # mesh points in space
    t = np.linspace(0, T, max_t+1)
    jarray = np.zeros(x.size)        # u at current time step
    jarray1 = np.zeros(x.size)

    #Calculate initial conditions
    for i in range(0, max_x+1):
        jarray[i] = pde(x[i])

    deltax = x[1] - x[0]            # gridspacing in x
    deltat = t[1] - t[0]            # gridspacing in t
    lmbda = kappa*deltat/(deltax**2)

    if bc_type == None:
        print("Please choose a boundary condition type")
        bc_type = input("dirichlet, or neumann")

    if bc_type == 'dirichlet':
        a = -lmbda * np.ones(max_x-1)
        b = (1+2*lmbda)*np.ones(max_x-1)
        c = a
        mtrx = np.array([a, b, c])
        pos = [-1, 0, 1]
        A_BE = sp.sparse.spdiags(mtrx, pos, max_x-1, max_x-1).todense()

        for j in range(0, max_t):
            p_j = bc1(t[j])
            q_j = bc2(t[j])
            b_array = np.zeros(jarray[1:-1].size)
            b_array[0] = p_j
            b_array[-1] = q_j
            jarray1[1:-1] = scipy.sparse.linalg.spsolve(A_BE, jarray[1:-1]+lmbda*b_array)

            #set boundary conditions
            jarray1[0] = p_j
            jarray1[-1] = q_j

            # Save u_j at time t[j+1]
            jarray[:] = jarray1[:]
        return x, jarray
    elif bc_type == 'neumann':
        a = -lmbda * np.ones(max_x+1)
        b = (1+2*lmbda)*np.ones(max_x+1)
        c = a

        a1 = np.zeros(max_x+1)
        a1[-2] = lmbda
        b1 = np.ones(max_x+1)
        c1 = np.zeros(max_x+1)
        c1[1] = lmbda

        mtrx1 = np.array([a1, b1, c1])
        mtrx = np.array([a, b, c])
        pos = [-1, 0, 1]
        A_BE = sp.sparse.spdiags(mtrx, pos, max_x+1, max_x+1).todense()
        A_BE1 = sp.sparse.spdiags(mtrx1, pos, max_x+1, max_x+1).todense()
        for j in range(0, max_t):
            p_j = bc1(t[j])
            q_j = bc2(t[j])
            b_array = np.zeros(jarray.size)
            b_array[0] = -2*deltax*p_j
            b_array[-1] = 2*deltax*q_j
            new_j = np.array(np.dot(A_BE1, jarray))[0]
            jarray1 = scipy.sparse.linalg.spsolve(A_BE, new_j+lmbda*b_array)

            # Save u_j at time t[j+1]
            jarray[:] = jarray1[:]
        return x, jarray
    else:
        raise ValueError('Boundary conditions must be either dirichlet or neumann')


def cn_main(max_x, max_t, T, L, pde, bcs, bc_type=None):
    bc1 = bcs[0]
    bc2 = bcs[1]
    if type(bc1) != types.FunctionType or type(bc2) != types.FunctionType:
        raise TypeError('Both Boundary Conditions must be of type function (lambda or defined), even if arbitrarily constant')
    x = np.linspace(0, L, max_x+1)     # mesh points in space
    t = np.linspace(0, T, max_t+1)
    jarray = np.zeros(x.size)        # u at current time step
    jarray1 = np.zeros(x.size)

    #Calculate initial conditions
    for i in range(0, max_x+1):
        jarray[i] = pde(x[i])

    deltax = x[1] - x[0]            # gridspacing in x
    deltat = t[1] - t[0]            # gridspacing in t
    lmbda = kappa*deltat/(deltax**2)
    if bc_type == None:
        print("Please choose a boundary condition type")
        bc_type = input("dirichlet, or neumann")
    if bc_type == 'dirichlet':
        a = -(lmbda/2) * np.ones(max_x-1)
        b = (1+lmbda)*np.ones(max_x-1)
        c = a
        b_b = (1-lmbda)*np.ones(max_x-1)

        mtrx_a = np.array([a, b, c])
        mtrx_b = np.array([-a, b_b, -c])
        pos = [-1, 0, 1]
        A_CN = sp.sparse.spdiags(mtrx_a, pos, max_x-1, max_x-1).todense()
        B_CN = sp.sparse.spdiags(mtrx_b, pos, max_x-1, max_x-1).todense()
        for i in range(0, max_x+1):
            jarray[i] = pde(x[i]) #Calcs u_I at each x point
        # print(jarray.reshape(1, -1))
        for j in range(max_t):
            pj = bc1(t[j])
            pj1 = bc1(t[j+1])
            qj = bc2(t[j])
            qj1 = bc2(t[j+1])
            b_array = np.dot(B_CN, jarray[1:-1])
            bc_array = np.zeros(b_array.size)
            bc_array[0] = pj + pj1
            bc_array[-1] = qj + qj1
            b_array += bc_array
            #b_array is of the form matrix due to dot function, hence convert it to an array
            b_array = np.asarray(b_array)

            jarray1[1:-1] = scipy.sparse.linalg.spsolve(A_CN, b_array[0])

            #BCs
            jarray1[0] = pj
            jarray1[max_x] = qj

            # Save u_j at time t[j+1]
            jarray[:] = jarray1[:]
        return x, jarray

    elif bc_type == 'neumann':
        a = -(lmbda/2) * np.ones(max_x+1)
        a[-2] = -lmbda
        b = (1+lmbda)*np.ones(max_x+1)
        c = -(lmbda/2) * np.ones(max_x+1)
        c[1] = -lmbda

        a_b = (lmbda/2) * np.ones(max_x+1)
        a_b[-2] = lmbda
        b_b = (1-lmbda)*np.ones(max_x+1)
        c_b = (lmbda/2) * np.ones(max_x+1)
        c_b[1] = lmbda

        mtrx_a = np.array([a, b, c])
        mtrx_b = np.array([a_b, b_b, c_b])
        pos = [-1, 0, 1]
        A_CN = sp.sparse.spdiags(mtrx_a, pos, max_x+1, max_x+1).todense()
        B_CN = sp.sparse.spdiags(mtrx_b, pos, max_x+1, max_x+1).todense()
        for j in range(max_t):
            pj = bc1(t[j])
            pj1 = bc1(t[j+1])
            qj = bc2(t[j])
            qj1 = bc2(t[j+1])
            b_array = np.array(np.dot(B_CN, jarray))[0]
            bc_vec = np.zeros(jarray.size)
            bc_vec[1] = -(pj + pj1)
            # bc_vec[-1] = qj + qj1
            b_array += (deltax*lmbda*bc_vec)
            jarray1 = sp.sparse.linalg.spsolve(A_CN, b_array)

            jarray[:] = jarray1[:]

        return x, jarray
    else:
        raise ValueError('Boundary conditions must be either dirichlet or neumann')


def finite_diff(pde, max_x, max_t, T, L, bcs, discretisation = None, bc_type = None):
    if discretisation == None:
        print("Please choose a Discretisation")
        discretisation = input("forward, backward or cn?")

    if discretisation == 'forward':
        discretisation = forward_euler_main
    elif discretisation == 'backward':
        discretisation = backwards_euler_main
    elif discretisation == 'cn':
        discretisation = cn_main
    else:
        print("Invalid discretisation\nPlease choose forward, backward, or cn")
        return -1
    x, jarr = discretisation(max_x, max_t, T, L, pde, bcs, bc_type)
    return x, jarr


def get_slope(error, delta):
    X = np.array(delta)
    Y = np.array(error)
    model = LinearRegression()
    model.fit(X.reshape(-1, 1), Y)
    return model.coef_


L = 5       # length of spatial domain
T = 5
# Set numerical parameters
mx = 50   # number of gridpoints in space
mt = 1000  # number of gridpoints in time

x = np.linspace(0, L, mx+1)     # mesh points in space
t = np.linspace(0, T, mt+1)
jarray = np.zeros(x.size, dtype=float)        # u at current time step
jarray1 = np.zeros(x.size, dtype= float)

#Calculate initial conditions
for i in range(0, mx+1):
    jarray[i] = u_I(x[i])


deltax = x[1] - x[0]            # gridspacing in x
deltat = t[1] - t[0]            # gridspacing in t
lmbda = kappa*deltat/(deltax**2)

print(deltat, deltax, lmbda)

a = -(lmbda/2) * np.ones(mx-1)
b = (1+lmbda)*np.ones(mx-1)
c = a
b_b = (1-lmbda)*np.ones(mx-1)

mtrx_a = np.array([a, b, c])
mtrx_b = np.array([-a, b_b, -c])
mtrx_c = np.array([np.ones(mx-1), -2*np.ones(mx-1), np.ones(mx-1)])
pos = [-1, 0, 1]
A_CN = sp.sparse.spdiags(mtrx_a, pos, mx-1, mx-1).todense()
B_CN = sp.sparse.spdiags(mtrx_b, pos, mx-1, mx-1).todense()
D_CN = sp.sparse.spdiags(mtrx_c, pos, mx-1, mx-1).todense()

heat = lambda u: 1 - u**2

def test(uj1):
    D1 = np.array(np.dot(D_CN, uj1))[0]
    F1 = heat(uj1)
    j1terms = uj1 - (lmbda/2)*D1 - (deltat/2)*F1

    D = np.array(np.dot(D_CN, jarray[1:-1]))[0]
    F = heat(jarray[1:-1])
    jterms = jarray[1:-1] + (lmbda/2)*D + (deltat/2)*F
    sol = j1terms - jterms
    return sol


for step in range(mt):
    rhs = np.array(np.dot(B_CN, jarray[1:-1]))
    jarray1[1:-1] = rhs + deltat*heat(jarray[1:-1])

    # jarray1[1:-1] = sp.sparse.linalg.spsolve(A_CN, rhs[0])
    jarray1[0] = 0
    jarray1[-1] = 0

    jarray[:] = jarray1[:]

plt.plot(x, jarray)
plt.show()

b1test = lambda t: 0
b2test = lambda t: 0

X, u_j = finite_diff(u_I, mx, mt, T, L, [b1test, b2test], bc_type='dirichlet', discretisation='cn')
#
# xx = np.linspace(0, L, 250)
# U_Exact = u_exact(xx, T)
#
#
# #Plot the final result and exact solution
plt.plot(X,u_j,'rx',label='num')
# plt.plot(X, 0.2*np.ones(X.size), 'k--', linewidth = 1)
# #
# # plt.plot(xx,u_exact(xx,T),'b-',label='exact')
# plt.xlabel('X')
# plt.ylabel('u(x,0.5)')
# plt.legend(loc='upper right')
plt.show()


# Errors = []
# Errors1 = []
# delt = []
# for n in range(25):
#     tempdel = T/mt
#     X, u_j = finite_diff(u_I, mx, mt, T, L, discretisation='cn')
#     X1, u_j1 = finite_diff(u_I, mx, mt, T, L, discretisation='backward')
#     Max_Error = abs(np.max(u_j) - np.max(U_Exact))
#     MaxE1 = abs(np.max(u_j1) - np.max(U_Exact))
#     Errors.append(Max_Error)
#     Errors1.append(MaxE1)
#     delt.append(tempdel)
#     mt += 50
#
#
# for e in range(len(Errors)):
#     Errors[e] = log2(Errors[e])
#     Errors1[e] = log2(Errors1[e])
#     delt[e] = log2(delt[e])
#
#
# plt.plot(delt, Errors, label='CN')
# plt.plot(delt, Errors1, 'r-', label= 'BWDs')
# plt.legend()
# plt.xlabel('log2(delta_t)')
# plt.ylabel('log2(abs_error)')
# plt.show()
#
# slope = get_slope(Errors, delt)
# slope1 = get_slope(Errors1, delt)
# print("Slope for cn:", slope)
# print("Slope for bwd:", slope1)

# print(ah)
